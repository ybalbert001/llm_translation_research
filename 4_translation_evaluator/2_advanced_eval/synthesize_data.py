#!/usr/bin/env python3
"""
Script to synthesize data for translation evaluation training.
This script traverses all files in the specified S3 bucket path and
performs data synthesis for files with fewer than 100 data points.
"""

import argparse
import json
import os
import random
import math
import boto3
from botocore.exceptions import ClientError
import logging
import time
import fnmatch
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import tempfile
from dify_helper import DifyHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SYNTHETIC_WORKFLOW_URL='http://dify-alb-1-281306538.us-west-2.elb.amazonaws.com/v1/workflows/run'
SYNTHETIC_WORKFLOW_KEY='app-xoGoDQGrRY3O4CT4MfsqEip3'

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Synthesize data for translation evaluation training')
    parser.add_argument(
        '--input_dir',
        type=str,
        default='s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/dataset/',
        help='S3 directory containing the dataset files'
    )
    parser.add_argument(
        '--target_count',
        type=int,
        default=5,
        help='Minimum number of samples required per file'
    )
    parser.add_argument(
        '--max_workers',
        type=int,
        default=1,
        help='Maximum number of worker threads'
    )
    return parser.parse_args()

def list_s3_files(bucket, prefix):
    """List all files in an S3 bucket with the given prefix."""
    s3_client = boto3.client('s3')
    paginator = s3_client.get_paginator('list_objects_v2')
    
    file_list = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                if not obj['Key'].endswith('/'):  # Skip directories
                    file_list.append(obj['Key'])
    
    return file_list

def check_file_exists(bucket_name, file_key):
    """
    检查 S3 中的文件是否存在
    
    :param bucket_name: S3 桶名称
    :param file_key: 文件的键（路径和文件名）
    :return: 如果文件存在返回 True，否则返回 False
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            # 文件不存在
            return False
        else:
            # 发生其他错误
            raise

def check_file_pattern_exists(bucket_name, prefix, filename_pattern):
    """
    检查 S3 桶中是否存在符合指定前缀和通配符模式的文件
    
    :param bucket_name: S3 桶名称
    :param prefix: 文件键的前缀
    :param filename_pattern: 文件名的通配符模式（不包含路径）
    :return: 如果存在符合前缀和模式的文件返回 True，否则返回 False
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' in response:
            # 过滤出符合通配符模式的文件
            for obj in response['Contents']:
                # 提取文件名部分（去掉路径）
                key = obj['Key']
                filename = key.split('/')[-1]
                
                if fnmatch.fnmatch(filename, filename_pattern):
                    return True
            
            # 如果没有找到符合模式的文件
            return False
        else:
            return False
    except ClientError as e:
        # 处理可能的错误
        print(f"Error checking prefix: {e}")
        return False


def download_s3_file(bucket, key, local_path):
    """Download a file from S3 to a local path."""
    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, key, local_path)

def upload_s3_file(local_path, bucket, key):
    """Upload a local file to S3."""
    s3_client = boto3.client('s3')
    s3_client.upload_file(local_path, bucket, key)

def synthesize_data(dify_helper, examples, target_count, max_retries=3, base_delay=1):
    """
    Synthesize additional data with dify worlflow.

    Args:
        dify_helper: Helper object for invoking the workflow
        examples: List of examples to sample from
        target_count: Target count of data to synthesize
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay for exponential backoff in seconds (default: 1)

    Returns:
        List of synthesized data records or empty list if all attempts fail
    """
    sampled_examples = random.sample(examples, 1)

    record = {
        "target_cnt": target_count,
        "examples" : json.dumps(sampled_examples, ensure_ascii=False)
    }

    retry_count = 0
    output = None

    while retry_count <= max_retries:
        try:
            output = dify_helper.invoke_workflow(record)
            if output and 'records' in output:
                return json.loads(output['records'])
            # else:
                print(f"Attempt {retry_count + 1}/{max_retries + 1}: Invalid output format")
        except Exception as e:
            print(f"Attempt {retry_count + 1}/{max_retries + 1}: Error occurred - {str(e)}")

        # If we've reached max retries, break out of the loop
        if retry_count >= max_retries:
            break

        # Calculate delay with exponential backoff and jitter
        delay = base_delay * (2 ** retry_count) + random.uniform(0, 0.5)
        print(f"Retrying in {delay:.2f} seconds...")
        time.sleep(delay)
        retry_count += 1

def process_file(file_info):
    """Process a single file, synthesizing data if needed."""
    bucket = file_info['bucket']
    key = file_info['key']
    target_count = file_info['target_count']

    def get_synthetic_filename(key, record_cnt):
        parts = os.path.basename(key).split('-')
        parts[-1] = f"{record_cnt}.json"
        synthetic_filename = "-".join(parts)
        prefix = '/'.join(key.split('/')[:-2])
        synthetic_file_key = f"{prefix}/synethic/{synthetic_filename}"
        return synthetic_file_key

    def get_synthetic_filename_pattern(key):
        parts = os.path.basename(key).split('-')
        parts[-1] = f"*.json"
        filename_pattern = "-".join(parts)
        prefix = '/'.join(key.split('/')[:-2])
        synthetic_file_prefix = f"{prefix}/synethic/"
        return synthetic_file_prefix, filename_pattern      
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        local_path = temp_file.name
    
    dify_helper = DifyHelper(SYNTHETIC_WORKFLOW_URL, SYNTHETIC_WORKFLOW_KEY) 
    try:
        # Download the file
        download_s3_file(bucket, key, local_path)
        
        # Read the data
        with open(local_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                # Try reading as JSONL
                f.seek(0)
                data = [ json.loads(line) for line in f if line.strip() ]
        
        # Check if we need to synthesize data
        if isinstance(data, list):
            logger.info(f"File {key} has {len(data)} samples, synthesizing to {target_count}")
            record_count_needed = target_count - len(data)
            # synthetic_file_key = get_synthetic_filename(key, target_count)
            synthetic_file_prefix, filename_pattern = get_synthetic_filename_pattern(key)
            # if check_file_exists(bucket, synthetic_file_key) == True:
            #     logger.info(f"s3://{bucket}/{synthetic_file_key} is already existed.")
            #     return
            if check_file_pattern_exists(bucket, synthetic_file_prefix, filename_pattern):
                logger.info(f"s3://{bucket}/{synthetic_file_prefix}{filename_pattern} is already existed.")
                return

            all_records = []
            # Synthesize data
            min_batch_size = 5
            batch_cnt = math.ceil(target_count / min_batch_size)
            for idx in range(batch_cnt):
                logger.info(f"synthesizing {idx}-th batch of {key}...")
                records = synthesize_data(dify_helper, data, min_batch_size)
                if records and len(records) > 1:
                    all_records.extend(records)
            
            # Write the synthesized data back
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
            
            # Upload the file back to S3
            synthetic_file_key = get_synthetic_filename(key, len(all_records))
            upload_s3_file(local_path, bucket, synthetic_file_key)
            
            logger.info(f"upload {local_path} to s3://{bucket}/{synthetic_file_key} successfully")
    
    finally:
        # Clean up the temporary file
        if os.path.exists(local_path):
            os.unlink(local_path)

def main():
    """Main function to run the data synthesis process."""
    args = parse_args()
    
    # Parse S3 URI
    if args.input_dir.startswith('s3://'):
        parts = args.input_dir[5:].split('/', 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ''
    else:
        logger.error("Input directory must be an S3 URI")
        return
    
    # List all files in the S3 bucket
    logger.info(f"Listing files in {args.input_dir}")
    files = list_s3_files(bucket, prefix)
    logger.info(f"Found {len(files)} files")
    
    # Prepare file info for processing
    file_infos = [
        {
            'bucket': bucket,
            'key': key,
            'target_count': args.target_count
        }
        for key in files
    ]
    
    # Process files in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for result in tqdm(executor.map(process_file, file_infos), total=len(file_infos)):
            results.append(result)

if __name__ == "__main__":
    main()
