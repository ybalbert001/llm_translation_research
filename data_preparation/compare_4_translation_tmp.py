from smart_open import smart_open
import json
import boto3
import csv
from urllib.parse import urlparse

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

def parse_llm_output_nova(item:dict):
    """Parse LLM output."""
    prompt = item["modelInput"]["messages"][0]['content'][0]['text']
    #extract content between in <src> and </src>
    idx =  prompt.rfind('<src>')
    src = prompt[idx:].split('<src>')[1].split('</src>')[0]

    translation = item["modelOutput"]['output']['message']["content"][0]['text']
    record_id = item["recordId"]

    return record_id, src, translation

def process_file_pair(haiku_path, c35_path, nova_pro_path, haiku35_path, nova_lite_path):
    """Process a pair of files and return aligned translations."""
    
    # First, load all c35 translations into memory
    aligned_translations = {}
    for item in read_jsonl_from_s3(c35_path):
        record_id, src, translation = parse_llm_output(item)
        aligned_translations[record_id] = {
            'source': src,
            'c35_translation': translation
        }

    print("load c35_translation done")

    # Process haiku translations and match with c35 translations
    for haiku_item in read_jsonl_from_s3(haiku_path):
        record_id, haiku_src, haiku_translation = parse_llm_output(haiku_item)
        assert record_id in aligned_translations.keys()
        
        aligned_translations[record_id]['haiku3_translation'] = haiku_translation
        
    print("load haiku3_translation done")

    # Process nova-pro translations and match with c35 translations
    for nova_pro_item in read_jsonl_from_s3(nova_pro_path):
        record_id, nova_pro_src, nova_pro_translation = parse_llm_output_nova(nova_pro_item)
        assert record_id in aligned_translations.keys()

        aligned_translations[record_id]['nova_pro_translation'] = nova_pro_translation

    print("load nova_pro_translation done")

    for nova_lite_item in read_jsonl_from_s3(nova_lite_path):
        record_id, nova_lite_src, nova_lite_translation = parse_llm_output_nova(nova_lite_item)
        assert record_id in aligned_translations.keys()

        aligned_translations[record_id]['nova_lite_translation'] = nova_lite_translation

    print("load nova_lite_translation done")

    # Process haiku35 translations and match with c35 translations
    for haiku35_item in read_jsonl_from_s3(haiku35_path):
        record_id, haiku35_src, haiku35_translation = parse_llm_output(haiku35_item)
        assert record_id in aligned_translations.keys()
        aligned_translations[record_id]['haiku35_translation'] = haiku35_translation

    rows = [ [k, v['source'], v['c35_translation'], v['haiku3_translation'], v['nova_pro_translation'], v['haiku35_translation'], v['nova_lite_translation'] ] for k, v in aligned_translations.items()]

    print("load haiku35_translation done")

    return rows

def main():
    haiku3_path='s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/3kl537z4ojex/meta_All_Beauty_0.jsonl.out'
    c35_path = 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/os8h3hdcfjnz/meta_All_Beauty_0.jsonl.out'
    nova_pro_path = 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/nova-pro/meta_All_Beauty_0.jsonl.out'
    haiku35_path = 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku35/tpplaq6vfh4p/meta_All_Beauty_0.jsonl.out'
    nova_lite_path = 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/nova-lite/meta_All_Beauty_0.jsonl.out'
    aligned_translations = process_file_pair(haiku3_path, c35_path, nova_pro_path, haiku35_path, nova_lite_path)

    # Write results to CSV
    filename = haiku3_path.split('/')[-1].split('.')[0]
    output_file = f'{filename}_translation_comparison.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames=['record_id','source', 'c35_translation', 'haiku3_translation', 'nova_pro_translation', 'haiku35_translation', 'nova_lite_translation']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        dict_rows = []
        for row in aligned_translations:
            dict_row = dict(zip(fieldnames, row))
            dict_rows.append(dict_row)
        
        writer.writerows(dict_rows)

    print(f"Results written to {output_file}")

if __name__ == "__main__":
    main()

