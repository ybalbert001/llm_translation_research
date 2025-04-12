## Todo

import boto3
import json
import sys
import os
from pathlib import Path
from io import BytesIO


# Add the parent directory to sys.path to import metric_based_evalution
script_dir = Path(__file__).parent
parent_dir = script_dir.parent
sys.path.append(str(script_dir))
sys.path.append(str(parent_dir))

s3_client = boto3.client('s3')

def list_s3_files(bucket_name, prefix):
    """
    List all jsonl.out files in the S3 bucket with the given prefix
    
    Args:
        bucket_name (str): S3 bucket name
        prefix (str): S3 prefix path
    
    Returns:
        list: List of S3 keys for jsonl.out files
    """
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # List objects in the bucket with the given prefix
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    
    jsonl_out_files = []
    
    # Check if there are any objects
    if 'Contents' in response:
        for obj in response['Contents']:
            # Check if the object has jsonl.out suffix
            if obj['Key'].endswith('jsonl.out'):
                jsonl_out_files.append(obj['Key'])
    
    return jsonl_out_files

def parse_s3_jsonl_files(bucket_name, file_keys):
    """
    Parse jsonl files directly from S3 and extract translation data
    
    Args:
        bucket_name (str): S3 bucket name
        file_keys (list): List of S3 keys for jsonl files
    
    Returns:
        tuple: (references_list, hypotheses_list) for evaluate_translation function
    """
    records = []

    # Initialize S3 client
    
    
    for file_key in file_keys:
        print(f"Parsing S3 file: s3://{bucket_name}/{file_key}")
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')

        # Process each line
        for line in content.splitlines():
            if not line.strip():
                continue
                
            try:
                data = json.loads(line.strip())
                # Extract reference (human translation) and hypothesis (machine translation)
                if data and 'modelOutput' in data and data['modelOutput']:
                    label = data['modelOutput']['label']
                    source = data['modelOutput']['source']
                    translation = data['modelOutput']['translation']
                else:
                    print(f"skip line: {line}")
                    continue

                records.append(json.dumps({"label":label, "source":source, "translation":translation}, ensure_ascii=False))

            except (json.JSONDecodeError, KeyError) as e:
                # import traceback
                print(f"Error parsing line: {e}")
                print(f"line: {line}")
                # traceback.print_exc()
                continue
    
    return records

def main():
    """Main function to process translation files and evaluate them"""
    # S3 configuration
    bucket_name = "translation-quality-check-model-sft-20241203"
    prefix = "amazon-review-product-meta-data/retrieval_based_translation/Game/kaggle_genshin/translation_files/outputs/"
    output_dir = "amazon-review-product-meta-data/retrieval_based_translation/Game/kaggle_genshin/translation_files/evaluations/inputs/"

    try:
        # List files from S3
        print(f"Listing files from s3://{bucket_name}/{prefix}")
        file_keys = list_s3_files(bucket_name, prefix)
        
        if not file_keys:
            print("No jsonl.out files found in the specified S3 location.")
            return
        
        print(f"Found {len(file_keys)} jsonl.out files.")

        # Parse files directly from S3
        for file_key in file_keys:
            records = parse_s3_jsonl_files(bucket_name, [file_key])
            
            print(f"Extracted {len(records)} translation pairs.")
            output_file = os.path.basename(file_key)
            filename = output_file.split('.')[0] + ".jsonl"
            s3_output_key = f"{output_dir}{filename}"

            s3_client.put_object(
                Body="\n".join(records),
                Bucket=bucket_name,
                Key=s3_output_key,
                ContentType='application/jsonl'
            )

            print(f"Evaluation complete. Results saved to {output_file}")
            
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
