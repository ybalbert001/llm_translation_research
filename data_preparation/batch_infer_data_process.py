import json
import pandas as pd
import os
import boto3
import argparse
from urllib.parse import urlparse
import io

def parse_s3_path(s3_path):
    """Parse S3 path into bucket and key."""
    parsed = urlparse(s3_path)
    if not parsed.netloc:
        raise ValueError(f"Invalid S3 path: {s3_path}")
    return parsed.netloc, parsed.path.lstrip('/')

def read_csv_from_s3(s3_path):
    """Read CSV file from S3."""
    s3_client = boto3.client('s3')
    bucket, key = parse_s3_path(s3_path)
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return pd.read_csv(io.BytesIO(response['Body'].read()))
    except Exception as e:
        raise Exception(f"Error reading CSV from S3: {str(e)}")

def write_jsonl_to_s3(records, s3_path):
    """Write records to JSONL file in S3."""
    s3_client = boto3.client('s3')
    bucket, key = parse_s3_path(s3_path)
    
    try:
        content = '\n'.join(json.dumps(record, ensure_ascii=False) for record in records)
        s3_client.put_object(Bucket=bucket, Key=key, Body=content.encode('utf-8'))
    except Exception as e:
        raise Exception(f"Error writing to S3: {str(e)}")

def list_s3_files(s3_path_pattern):
    """List S3 files matching the pattern."""
    s3_client = boto3.client('s3')
    # 只替换到最后一个/之前的部分
    last_slash_index = s3_path_pattern.rfind('/')
    base_pattern = s3_path_pattern[:last_slash_index+1]
    file_pattern = s3_path_pattern[last_slash_index+1:]
    bucket, prefix = parse_s3_path(base_pattern)
    print(f"Searching in bucket: {bucket}, prefix: {prefix}")
    print(f"File pattern: {file_pattern}")
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        files = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' in page:
                # 使用文件模式过滤文件
                import fnmatch
                new_files = []
                for obj in page['Contents']:
                    file_name = obj['Key'].split('/')[-1]
                    if fnmatch.fnmatch(file_name, file_pattern):
                        new_files.append(f"s3://{bucket}/{obj['Key']}")
                print(f"Found {len(new_files)} matching files in current page")
                files.extend(new_files)
            else:
                print("No contents found in current page")
        
        if not files:
            print(f"No files found matching pattern: {s3_path_pattern}")
        return files
    except Exception as e:
        print(f"Error listing S3 files: {str(e)}")
        raise

def process_csv_file(input_s3_path, output_s3_path, target_lang):
    """Process a single CSV file from S3 and write results to S3."""
    print(f"Processing {input_s3_path}")
    
    # Read CSV file from S3
    df = read_csv_from_s3(input_s3_path)
    
    # Create base name for record IDs
    base_name = os.path.splitext(os.path.basename(input_s3_path))[0]
    
    # Process records
    records = []
    for idx, row in df.iterrows():
        record_id = f"{base_name}_{idx}"
        title = row[0]
        record = {
            "recordId": f"{record_id}", 
            "modelInput": {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": 2048,
                "stop_sequences": ['</translation>'],
                "messages": [ 
                    { 
                        "role": "user", 
                        "content": [
                            {
                                "type": "text", 
                                "text": f"你是一位翻译专家，擅长翻译商品title。请精准的把<src>中的商品Title翻译为{target_lang}, 输出到<translation> xml tag中。\n<src>{title}</src>\n" 
                            } 
                        ]
                    },
                    { 
                        "role": "assistant", 
                        "content": [
                            {
                                "type": "text", 
                                "text": "<translation>" 
                            } 
                        ]
                    }
                ]
            }
        }
        records.append(record)
    
    # Write to S3
    write_jsonl_to_s3(records, output_s3_path)
    print(f"Written output to {output_s3_path}")

def main():
    parser = argparse.ArgumentParser(description='Process CSV files for translation')
    parser.add_argument('--target-lang', type=str, default='zh-cn',
                      help='Target language for translation (default: zh-cn)')
    args = parser.parse_args()

    try:
        # S3 paths configuration
        input_patterns = [
            "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/meta_*.csv"
        ]

        output_prefix = f"s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/{args.target_lang}/"

        print(f"Target language: {args.target_lang}")
        for pattern in input_patterns:
            print(f"Looking for files matching pattern: {pattern}")
            # List matching input files
            input_files = list_s3_files(pattern)
            print(f"Found {len(input_files)} matching files")
            
            # Process each file
            for input_file in input_files:
                try:
                    # Create output path
                    base_name = os.path.splitext(os.path.basename(input_file))[0]
                    output_path = f"{output_prefix}{base_name}.jsonl"
                    
                    # Process the file
                    process_csv_file(input_file, output_path, args.target_lang)
                except Exception as e:
                    print(f"Error processing file {input_file}: {str(e)}")
    except Exception as e:
        print(f"Main execution error: {str(e)}")

if __name__ == '__main__':
    main()
