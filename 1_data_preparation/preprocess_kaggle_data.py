#!/usr/bin/env python3
"""
Script to preprocess Genshin Impact Japanese-Chinese translation data from Kaggle.
Reads parquet files from the specified input directory (defaults to dataset/genshin-impact-ja-zh)
and outputs processed data in JSON format to an S3 bucket.

Usage:
    python preprocess_kaggle_data.py [--input-dir INPUT_DIR]
"""

import os
import json
import pandas as pd
import boto3
from pathlib import Path
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_INPUT_DIR = Path("../dataset/genshin-impact-ja-zh")
S3_OUTPUT_PATH = "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/kaggle"

def read_parquet_files(input_dir):
    """
    Read all parquet files from the input directory.
    
    Args:
        input_dir (Path): Path to the directory containing parquet files
    
    Returns:
        dict: Dictionary containing DataFrames for each parquet file
    """
    input_dir_obj = Path(input_dir)
    parquet_files = list(input_dir_obj.glob("*.parquet"))
    logger.info(f"Found {len(parquet_files)} parquet files: {[f.name for f in parquet_files]}")

    for file_path in parquet_files:
        file_name = file_path.stem
        logger.info(f"Reading {file_path}")
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"Successfully read {file_name} with shape {df.shape}")
            yield file_name, df
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

def process_data(df):
    """
    Process the dataframes into the required JSON format.
    
    Args:
        dataframes (dict): Dictionary of dataframes
        
    Returns:
        list: List of JSON records
    """
    records = []
    for _, row in df.iterrows():
        if 'ja' in df.columns and 'zh' in df.columns:
            record = {
                "english": str(row.get('en', '')),
                "japanese": row.get('ja', ''),
                "chinese": row.get('zh', ''),
            }
            records.append(record)

    logger.info(f"Processed {len(records)} total records")
    return records

def upload_to_s3(records, s3_path):
    """
    Upload the processed records to S3 in JSON format.
    
    Args:
        records (list): List of JSON records
    """
    # Parse S3 bucket and prefix from S3_OUTPUT_PATH
    s3_headless_path = s3_path.replace("s3://", "")
    bucket_name = s3_headless_path.split("/")[0]
    prefix = "/".join(s3_headless_path.split("/")[1:])
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    json_data = json.dumps(records, ensure_ascii=False, indent=2)
        
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=prefix,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")

def main():
    """Main function to orchestrate the data processing and upload."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Preprocess Genshin Impact Japanese-Chinese translation data.')
    parser.add_argument('--input_dir', type=str, default=str(DEFAULT_INPUT_DIR),
                        help=f'Input directory containing parquet files (default: {DEFAULT_INPUT_DIR})')
    parser.add_argument('--output_dir', type=str, default=str(S3_OUTPUT_PATH),
                        help=f'Output directory containing parquet files (default: {S3_OUTPUT_PATH})')
    args = parser.parse_args()
    
    # Set input directory from arguments
    input_dir = args.input_dir
    output_dir = args.output_dir
    logger.info(f"Using input directory: {input_dir}")
    
    logger.info("Starting Kaggle data preprocessing")

    for file_name, df in read_parquet_files(input_dir):
        output_path = f"{output_dir}/{file_name}.json"
        records = process_data(df)
        logger.info(f"uploading Kaggle data to {output_path}")
        upload_to_s3(records, output_path)
    
    logger.info("Kaggle data preprocessing completed")

if __name__ == "__main__":
    main()
