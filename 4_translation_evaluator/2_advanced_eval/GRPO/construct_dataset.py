#!/usr/bin/env python3
"""
Script to convert JSON data from S3 to Parquet format and write back to S3.
"""
import os
import boto3
import pandas as pd
import json
import tempfile
import argparse
from tqdm import tqdm

def download_s3_files(s3_path):
    """Download files from S3 to a temporary directory."""
    s3_client = boto3.client('s3')
    
    # Parse bucket and prefix from s3_path
    path_parts = s3_path.replace("s3://", "").split("/")
    bucket = path_parts[0]
    prefix = "/".join(path_parts[1:-1])
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    print(f"Downloading files from s3://{bucket}/{prefix} to {temp_dir}")
    
    # List objects in the bucket with the given prefix
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    
    downloaded_files = []
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.json'):
                    local_file = os.path.join(temp_dir, os.path.basename(key))
                    s3_client.download_file(bucket, key, local_file)
                    downloaded_files.append(local_file)
    
    print(f"Downloaded {len(downloaded_files)} files")
    return temp_dir, downloaded_files

def to_grpo(record):
    system = """You are an expert linguist specializing in translation quality assessment. Your task is to evaluate the translation produced by translation model. Assess the translation based on the following criteria:

1. Sensitive content should not be refused to translate
2. No non-target language word appears
3. No irrelevant or useless repetitive words.
4. No Spelling, abnormal symbols and grammar errors detected
5. Quantity, Quantifiers and Units are translated accurately
6. Format maintained between source and translation. No added numbering/bullet

The target language is zh-cn, please evaluate translation quality, and give your rating(0.0-5.0)."""
    problem = f"""Here is the source text in <src> tag and also its translation from an translator in <translation> tag. 
<src>
{record["source"]}
</src>

<translation>
{record["translation"]}
</translation>"""
    
    answer = f"<think>{record["thought"]}</think>, my ratings is {record["scores"]}"
    
    grpo_record = {
        'system': system,
        'problem': problem,
        'answer': answer,
    }
    return grpo_record

def process_json_files(json_files):
    """Process JSON files and convert to a pandas DataFrame."""
    all_data = []
    
    for file_path in tqdm(json_files, desc="Processing JSON files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    grpo_data = [ to_grpo(record) for record in all_data if "thought" in record and "scores" in record and "source" in record and "translation" in record ]


    print(f"Total records: {len(all_data)}")
    return pd.DataFrame(grpo_data)

def upload_to_s3(df, output_path):
    """Upload DataFrame as Parquet to S3."""
    s3_client = boto3.client('s3')
    
    # Parse bucket and key from output_path
    path_parts = output_path.replace("s3://", "").split("/")
    bucket = path_parts[0]
    key = "/".join(path_parts[1:])
    
    with tempfile.NamedTemporaryFile(suffix='.parquet') as tmp:
        df.to_parquet(tmp.name, index=False)
        print(f"Uploading parquet file to s3://{bucket}/{key}")
        s3_client.upload_file(tmp.name, bucket, key)
    
    print(f"Successfully uploaded data to {output_path}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert JSON data from S3 to Parquet format')
    parser.add_argument('--input', type=str, required=True,
                        help='Input S3 path with JSON files (e.g., s3://bucket/prefix/*.json)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output S3 path for Parquet file (e.g., s3://bucket/prefix/)')
    return parser.parse_args()

def main():
    """Main function to orchestrate the conversion process."""
    args = parse_arguments()
    print("Starting JSON to Parquet conversion process")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    
    # Download JSON files from S3
    temp_dir, json_files = download_s3_files(args.input)
    
    # Process JSON files
    df = process_json_files(json_files)
    
    # Upload as Parquet to S3
    upload_to_s3(df, args.output)
    
    # Clean up
    for file in json_files:
        os.remove(file)
    os.rmdir(temp_dir)
    
    print("Conversion completed successfully")

if __name__ == "__main__":
    main()