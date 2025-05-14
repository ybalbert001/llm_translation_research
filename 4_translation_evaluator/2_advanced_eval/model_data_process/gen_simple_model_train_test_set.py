#!/usr/bin/env python3
import boto3
import json
import os
import re
import random
from collections import defaultdict
import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import concurrent.futures

from utils import get_score_category

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Generate train and test sets from dataset')
    parser.add_argument('--origin_dataset', type=str, 
                        default='',
                        help='S3 path to the origin dataset')
    parser.add_argument('--synthetic_dataset', type=str, 
                        default='',
                        help='S3 path to the synthetic dataset')
    parser.add_argument('--output_dir', type=str, 
                        default='',
                        help='S3 path for the output train set')
    parser.add_argument('--output_bucket', type=str, 
                        default='translation-quality-check-model-sft-20241203',
                        help='S3 path for the output test set')
    parser.add_argument('--max_workers', type=int, default=1,
                        help='Maximum number of worker threads')
    parser.add_argument('--test_ratio', type=float, default=0.2,
                        help='the ratio of testset')
    return parser.parse_args()

def parse_s3_path(s3_path):
    """Parse S3 path into bucket and prefix."""
    path = s3_path.replace('s3://', '')
    bucket, prefix = path.split('/', 1)
    if not prefix.endswith('/'):
        prefix += '/'
    return bucket, prefix

def list_s3_files(bucket, prefix):
    """List all files in an S3 bucket with the given prefix."""
    s3_client = boto3.client('s3')
    files = []
    
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.json'):
                    files.append(obj['Key'])
    
    return files

def extract_file_prefix(file_key):
    filename = file_key.split('/')[-1]
    return filename.split('-')[0]

def download_and_read_json(bucket, key):
    """Download and read a JSON file from S3."""
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error downloading or parsing {key}: {e}")
        return None

def upload_json_to_s3(data, bucket, key):
    """Upload JSON data to S3."""
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(
            Body=json.dumps(data, ensure_ascii=False),
            Bucket=bucket,
            Key=key
        )
        logger.info(f"Successfully uploaded to s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"Error uploading to {key}: {e}")

def process_file_group(product_category, file_group, source_bucket):
    """Process a group of files with the same prefix."""
    pos_all_data = [[], [], [], [], [], [], []]
    neg_all_data = [[], [], [], [], [], [], []]
    stat_dict = {}
    max_record_count = 100
        
    # import pdb 
    # pdb.set_trace()
    # Download and merge all files in the group
    for file_key in file_group:
        data = download_and_read_json(source_bucket, file_key)
        for record in data:
            cate_id, min_score = get_score_category(record["scores"])
            score = int(min_score)
            key = f"{product_category}-cate-{cate_id}-score-{score}"
            if key not in stat_dict:
                stat_dict[key] = 0
            else:
                stat_dict[key] += 1

            if score in [3,4,5]:
                pos_all_data[cate_id].append(record)
            else:
                neg_all_data[cate_id].append(record)
    
    return pos_all_data, neg_all_data, stat_dict


def build_sft_dataset(trainset, bucket, s3_prefix_dir):
    s3_client = boto3.client('s3')
    for idx, cate_list in enumerate(trainset):
        train_example_list = []
        for item in cate_list:
            try:
                train_example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You are an expert linguist specializing in translation quality assessment. Your task is to evaluate the translation produced by translation model. Assess the translation based on the following criteria:

    1. Sensitive content should not be refused to translate
    2. No non-target language word appears
    3. No irrelevant or useless repetitive words.
    4. No Spelling, abnormal symbols and grammar errors detected
    5. Quantity, Quantifiers and Units are translated accurately
    6. Format maintained between source and translation. No added numbering/bullet

    The target language is zh-cn, please evaluate translation quality, and give your rating(0.0-5.0).
    """
                        },
                        {
                            "role": "user",
                            "content": f"""Here is the source text in <src> tag and also its translation from an translator in <translation> tag. 
    <src>
    {item["source"]}
    </src>

    <translation>
    {item["translation"]}
    </translation>"""
                        },
                        {
                            "role": "assistant",
                            "content": f"<think>{item["thought"]}</think>, my ratings is {item["scores"]}"
                        }
                    ]
                }
                train_example_list.append(train_example)
            except Exception as e:
                logger.info(f"exception: skip {train_example}")

        key = f"{s3_prefix_dir}/category-{idx}.json"
        s3_client.put_object(
            Body=json.dumps(train_example_list, ensure_ascii=False),
            Bucket=bucket,
            Key=key
        )
        logger.info(f"Successfully uploaded to s3://{bucket}/{key}")


def main():
    args = parse_args()

    # Group files by prefix
    file_groups = defaultdict(list)    

    if args.origin_dataset:
        origin_bucket, origin_prefix = parse_s3_path(args.origin_dataset)
        logger.info("Listing files from origin dataset...")
        origin_files = list_s3_files(origin_bucket, origin_prefix)
        logger.info(f"Found {len(origin_files)} files in origin dataset")
        for file_key in origin_files:
            prefix = extract_file_prefix(file_key)
            if prefix:
                file_groups[prefix].append(file_key)

    if args.synthetic_dataset:
        synthetic_bucket, synthetic_prefix = parse_s3_path(args.synthetic_dataset)
        logger.info("Listing files from synthetic dataset...")
        synthetic_files = list_s3_files(synthetic_bucket, synthetic_prefix)
        logger.info(f"Found {len(synthetic_files)} files in synthetic dataset")
    
        for file_key in synthetic_files:
            prefix = extract_file_prefix(file_key)
            if prefix:
                # Use the same bucket as the synthetic files are in
                file_groups[prefix].append(file_key)
    
    logger.info(f"Grouped files into {len(file_groups)} groups")

    pos_all_data = [[],[],[],[],[],[],[]]
    neg_all_data = [[],[],[],[],[],[],[]]
    all_stat_dict = {}
    # Process each group of files
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = []
        for prefix, file_group in file_groups.items():
            # Determine which bucket each file is in
            source_bucket = args.output_bucket

            future = executor.submit(
                process_file_group,
                prefix,
                file_group,
                source_bucket
            ) 
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            pos_records, neg_records, stat_dict = future.result()
            all_stat_dict.update(stat_dict)
            for idx, record_list in enumerate(pos_records):
                pos_all_data[idx].extend(record_list)
                random.shuffle(pos_all_data[idx])
            for idx, record_list in enumerate(neg_records):
                neg_all_data[idx].extend(record_list)
                random.shuffle(neg_all_data[idx])

        pos_cate_cnt_list = [ len(l) for l in pos_all_data ]
        neg_cate_cnt_list = [ len(l) for l in neg_all_data ]

    logger.info("Processing complete!")
    logger.info(f"pos_cate_cnt_list: \n {pos_cate_cnt_list}")
    logger.info(f"neg_cate_cnt_list: \n {neg_cate_cnt_list}")
    logger.info(f"all_stat_dict: \n {all_stat_dict}")

    s3 = boto3.client('s3')

    for idx, cate_list in enumerate(pos_all_data):
        obj_key = f"{args.output_dir}/pos_data/category-{idx}.json"
        logger.info(f"pos_data will save to ${obj_key}")

        s3.put_object(
            Bucket=args.output_bucket,
            Key=obj_key,
            Body=json.dumps(cate_list, ensure_ascii=False).encode('utf-8')
        )

    for idx, cate_list in enumerate(neg_all_data):
        obj_key = f"{args.output_dir}/neg_data/category-{idx}.json"
        logger.info(f"neg_data will save to ${obj_key}")

        s3.put_object(
            Bucket=args.output_bucket,
            Key=obj_key,
            Body=json.dumps(cate_list, ensure_ascii=False).encode('utf-8')
        )

    trainset = [[],[],[],[],[],[]]
    testset = [[],[],[],[],[],[]]
    for idx, cate_list in enumerate(neg_all_data):
        if idx < 6:
            total_cnt = len(cate_list[:200])
            train_neg_cnt = int(total_cnt * (1 - args.test_ratio))
            train_neg_samples = cate_list[:train_neg_cnt]
            trainset[idx].extend(train_neg_samples)
            train_pos_samples = pos_all_data[idx][:train_neg_cnt]
            trainset[idx].extend(train_pos_samples)

            testset[idx].extend(cate_list[train_neg_cnt:total_cnt])
            testset[idx].extend(pos_all_data[idx][train_neg_cnt:total_cnt])

    for idx, cate_list in enumerate(trainset):
        obj_key = f"{args.output_dir}/trainset/category-{idx}.json"
        logger.info(f"pos_data will save to ${obj_key}")

        s3.put_object(
            Bucket=args.output_bucket,
            Key=obj_key,
            Body=json.dumps(trainset[idx], ensure_ascii=False).encode('utf-8')
        )

    build_sft_dataset(trainset=trainset, bucket=args.output_bucket, s3_prefix_dir=f"{args.output_dir}/openai_trainset")

    for idx, cate_list in enumerate(testset):
        obj_key = f"{args.output_dir}/testset/category-{idx}.json"
        logger.info(f"neg_data will save to ${obj_key}")

        s3.put_object(
            Bucket=args.output_bucket,
            Key=obj_key,
            Body=json.dumps(testset[idx], ensure_ascii=False).encode('utf-8')
        )
    
if __name__ == "__main__":
    main()
