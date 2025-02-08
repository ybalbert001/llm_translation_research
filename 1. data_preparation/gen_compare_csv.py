from smart_open import smart_open
import json
import boto3
import csv
from urllib.parse import urlparse

# S3 paths
haiku_dir = 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/'
c35_dir = 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/'

def parse_s3_path(s3_path):
    """Parse S3 path into bucket and prefix."""
    parsed = urlparse(s3_path)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip('/')
    return bucket, prefix

def list_s3_jsonl_files(s3_path):
    """List all jsonl files in the given S3 path."""
    bucket, prefix = parse_s3_path(s3_path)
    s3 = boto3.client('s3')
    
    files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.jsonl.out'):
                    files.append(f"s3://{bucket}/{obj['Key']}")
    return files

def get_file_pairs(haiku_dir, c35_dir):
    """Get pairs of files with matching names from both directories."""
    haiku_files = list_s3_jsonl_files(haiku_dir)
    c35_files = list_s3_jsonl_files(c35_dir)
    
    # Create dictionaries with filename as key and full path as value
    haiku_dict = {path.split('/')[-1]: path for path in haiku_files}
    c35_dict = {path.split('/')[-1]: path for path in c35_files}
    
    # Find matching pairs
    pairs = []
    for filename in haiku_dict:
        if filename in c35_dict:
            pairs.append((haiku_dict[filename], c35_dict[filename]))
    
    return pairs

def read_jsonl_from_s3(s3_path):
    """Read JSONL file from S3 line by line."""
    with smart_open(s3_path, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                yield json.loads(line)

def parse_llm_output(item:dict):
    """Parse LLM output."""
    prompt = item["modelInput"]["messages"][0]['content'][0]['text']
    #extract content between in <src> and </src>
    idx =  prompt.rfind('<src>')
    src = prompt[idx:].split('<src>')[1].split('</src>')[0]

    translation = item["modelOutput"]["content"][0]['text']
    record_id = item["recordId"]

    return record_id, src, translation

def process_file_pair(haiku_path, c35_path):
    """Process a pair of files and return aligned translations."""
    aligned_translations = []
    
    # First, load all c35 translations into memory
    c35_translations = {}
    for item in read_jsonl_from_s3(c35_path):
        record_id, src, translation = parse_llm_output(item)
        c35_translations[record_id] = {
            'source': src,
            'translation': translation
        }

    # Process haiku translations and match with c35 translations
    for haiku_item in read_jsonl_from_s3(haiku_path):
        record_id, haiku_src, haiku_translation = parse_llm_output(haiku_item)
        
        if record_id in c35_translations:
            c35_data = c35_translations[record_id]
            # Verify that sources match
            assert haiku_src == c35_data['source'], f"Source mismatch for record {record_id}: {haiku_src} != {c35_data['source']}"
            
            aligned_translations.append({
                'source': haiku_src,
                'haiku3_translation': haiku_translation,
                'c35_translation': c35_data['translation']
            })
        else:
            print(f"Warning: Record {record_id} not found in C35 translations")

    return aligned_translations

def main():
    # Get file pairs
    pairs = get_file_pairs(haiku_dir, c35_dir)
    
    # Process all pairs and collect results
    for haiku_path, c35_path in pairs:
        print(f"Processing:")
        print(f"Haiku: {haiku_path}")
        print(f"C35: {c35_path}")
        translations = process_file_pair(haiku_path, c35_path)

        # Write results to CSV
        filename = haiku_path.split('/')[-1].split('.')[0]
        output_file = f'{filename}_translation_comparison.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['source', 'haiku3_translation', 'c35_translation'])
            writer.writeheader()
            writer.writerows(translations)

        print(f"Results written to {output_file}")

if __name__ == "__main__":
    main()
