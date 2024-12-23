"""
Setup Athena tables for translation quality evaluation data.

This script creates external tables in Amazon Athena to analyze batch inference results
from translation models. It handles complex nested JSON data structures and uses
the OpenX JSON SerDe for parsing.

Required AWS permissions:
- athena:StartQueryExecution
- athena:GetQueryExecution
- s3:PutObject (for query results)
- s3:GetObject (for reading data)
"""

import boto3
import argparse
import time
from botocore.exceptions import ClientError

# Create database if not exists
create_database = """
CREATE DATABASE IF NOT EXISTS {database}
COMMENT 'Database for translation quality evaluation data'
LOCATION 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/{database}/';
"""

nova_inference_table = """
CREATE EXTERNAL TABLE IF NOT EXISTS nova_inference_results (
    modelInput STRUCT<
        schemaVersion: STRING,
        system: ARRAY<STRUCT<
            text: STRING
        >>,
        inferenceConfig: STRUCT<
            max_new_tokens: INT,
            top_p: DOUBLE,
            top_k: INT,
            temperature: DOUBLE,
            stopSequences: ARRAY<STRING>
        >,
        messages: ARRAY<STRUCT<
            role: STRING,
            content: ARRAY<STRUCT<
                text: STRING
            >>
        >>
    >,
    modelOutput STRUCT<
        id: STRING,
        type: STRING,
        role: STRING,
        model: STRING,
        content: ARRAY<STRUCT<
            type: STRING,
            text: STRING
        >>,
        stop_reason: STRING,
        stop_sequence: STRING,
        usage: STRUCT<
            input_tokens: INT,
            output_tokens: INT
        >
    >,
    recordId STRING
)
PARTITIONED BY (
    model STRING,
    language STRING,
    job_id STRING,
    execution_id STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
STORED AS TEXTFILE
LOCATION 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/'
TBLPROPERTIES ('has_encrypted_data'='false');
"""

# Create table for batch inference results with partitions
claude_inference_table = """
CREATE EXTERNAL TABLE IF NOT EXISTS claude_inference_results (
    modelInput STRUCT<
        anthropic_version: STRING,
        max_tokens: INT,
        stop_sequences: ARRAY<STRING>,
        messages: ARRAY<STRUCT<
            role: STRING,
            content: ARRAY<STRUCT<
                type: STRING,
                text: STRING
            >>
        >>
    >,
    modelOutput STRUCT<
        id: STRING,
        type: STRING,
        role: STRING,
        model: STRING,
        content: ARRAY<STRUCT<
            type: STRING,
            text: STRING
        >>,
        stop_reason: STRING,
        stop_sequence: STRING,
        usage: STRUCT<
            input_tokens: INT,
            output_tokens: INT
        >
    >,
    recordId STRING
)
PARTITIONED BY (
    model STRING,
    language STRING,
    job_id STRING,
    execution_id STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
STORED AS TEXTFILE
LOCATION 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/'
TBLPROPERTIES ('has_encrypted_data'='false');
"""

# Add partitions query template
add_partition_claude_template = """
ALTER TABLE claude_inference_results ADD IF NOT EXISTS
PARTITION (model = 'haiku3', language = '{language}', job_id = '{job_id}', execution_id = '{execution_id}')
LOCATION 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/{language}/{job_id}/{execution_id}/';
"""
add_partition_nova_template = """
ALTER TABLE nova_inference_results ADD IF NOT EXISTS
PARTITION (model = 'novaLite', language = '{language}', job_id = '{job_id}', execution_id = '{execution_id}')
LOCATION 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/novaLite/{language}/{job_id}/{execution_id}/';
"""

def execute_query(client, query, database, s3_output, timeout=300):
    """Execute Athena query and wait for completion
    
    Args:
        client: boto3 Athena client
        query: SQL query string to execute
        database: Athena database name
        s3_output: S3 location for query results
        timeout: Maximum time to wait for query completion in seconds
    
    Raises:
        Exception: If query fails or times out
    """
    try:
        response = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': s3_output}
        )
        
        execution_id = response['QueryExecutionId']
        state = 'RUNNING'
        start_time = time.time()
        
        while state in ['RUNNING', 'QUEUED']:
            if time.time() - start_time > timeout:
                raise Exception(f"Query execution timed out after {timeout} seconds")
            
            # Wait before checking status again
            time.sleep(5)
            
            response = client.get_query_execution(QueryExecutionId=execution_id)
            state = response['QueryExecution']['Status']['State']
            
            if state == 'FAILED':
                raise Exception(response['QueryExecution']['Status']['StateChangeReason'])
            elif state == 'SUCCEEDED':
                print(f"Query {execution_id} completed successfully")
                
    except ClientError as e:
        raise Exception(f"AWS API error: {str(e)}")

def list_partitions(s3_client, bucket, prefix, progress_interval=100):
    """List all partitions by traversing S3 path structure
    
    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        prefix: S3 prefix to start listing from
        
    Returns:
        list: List of tuples (model, language, job_id, execution_id)
    """
    try:
        partitions = set()
        paginator = s3_client.get_paginator('list_objects_v2')
        file_count = 0
        
        # Remove bucket name from prefix if present
        if prefix.startswith(f"s3://{bucket}/"):
            prefix = prefix[len(f"s3://{bucket}/"):]
        
        print("Scanning S3 for .jsonl.out files...")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                # Skip if not a jsonl.out file
                if not obj['Key'].endswith('.jsonl.out'):
                    continue
                    
                file_count += 1
                if file_count % progress_interval == 0:
                    print(f"Processed {file_count} files...")
                    
                # Extract partition values from path
                # Example path: s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ru-ru/job_0/g6wcb1mwhc1d/meta_Appliances_0.jsonl.out
                parts = obj['Key'].split('/')
                if len(parts) >= 7:  # Ensure path has enough components
                    try:
                        model = parts[-5]  # haiku3
                        language = parts[-4]  # ru-ru
                        job_id = parts[-3]  # job_0
                        execution_id = parts[-2]  # g6wcb1mwhc1d
                        partitions.add((model, language, job_id, execution_id))
                    except IndexError:
                        print(f"Skipping malformed path: {obj['Key']}")
                    
        print(f"Finished processing {file_count} files")
        return list(partitions)
    except ClientError as e:
        print(f"Failed to list S3 objects: {str(e)}")
        return []

def add_partition(client, database, s3_output, model, language, job_id, execution_id):
    """Add a partition to the batch inference results table"""

    if model == 'haiku3':
        query = add_partition_claude_template.format(
            model=model,
            language=language,
            job_id=job_id,
            execution_id=execution_id
        )
        execute_query(client, query, database, s3_output)
    elif model == 'novaLite':
        query = add_partition_nova_template.format(
            model=model,
            language=language,
            job_id=job_id,
            execution_id=execution_id
        )
        execute_query(client, query, database, s3_output)

def main():
    parser = argparse.ArgumentParser(
        description='Setup Athena tables for translation quality evaluation data'
    )
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    parser.add_argument('--database', required=True, help='Athena database name')
    parser.add_argument('--athena_output', required=True, help='S3 output location for query results')
    parser.add_argument('--s3_bucket', default='translation-quality-check-model-sft-20241203', help='s3 bucket for table data')
    parser.add_argument('--s3_prefix', default='amazon-review-product-meta-data/batch-inference-output', help='S3 prefix path for table data')
    args = parser.parse_args()

    # Initialize AWS clients
    try:
        athena_client = boto3.client('athena', region_name=args.region)
        s3_client = boto3.client('s3', region_name=args.region)
    except ClientError as e:
        print(f"Failed to initialize AWS clients: {str(e)}")
        return 1
    
    # Create database
    print(f"Creating database {args.database}...")
    execute_query(athena_client, create_database.format(database=args.database), 'default', args.athena_output)
    
    # Create claude table
    print("Creating claude batch inference results table...")
    execute_query(athena_client, claude_inference_table, args.database, args.athena_output)

    # Create base table
    print("Creating nova batch inference results table...")
    execute_query(athena_client, nova_inference_table, args.database, args.athena_output)

    # Discover and add partitions
    bucket = args.s3_bucket
    prefix = args.s3_prefix
    print(f"Discovering partitions in s3://{bucket}/{prefix}...")
    
    partitions = list_partitions(s3_client, bucket, prefix)
    print(f"Found {len(partitions)} partitions")
    
    total_partitions = len(partitions)
    for i, (model, language, job_id, execution_id) in enumerate(partitions, 1):
        print(f"Adding partition {i}/{total_partitions} for model={model}, language={language}, job_id={job_id}, execution_id={execution_id}")
        add_partition(athena_client, args.database, args.athena_output, model, language, job_id, execution_id)

if __name__ == '__main__':
    main()
