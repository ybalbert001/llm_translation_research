# Bedrock Batch Inference Glue Job

This implementation provides a scalable solution for running batch inference using Amazon Bedrock through AWS Glue. The solution processes JSONL files from S3 and controls the rate of API calls to Bedrock.

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. Access to AWS Bedrock service
3. S3 bucket for storing Glue scripts and data
4. Python 3.9+ installed locally (for deployment script)

## Setup Instructions

1. First, upload the Glue job script to your S3 bucket:
```bash
aws s3 cp glue_bedrock_batch_inference.py s3://your-bucket/glue-scripts/
```

2. Install required Python packages for the deployment script:
```bash
pip install boto3
```

3. Deploy the Glue job using the deployment script:
```bash
python deploy_glue_job.py \
    --script-location s3://your-bucket/glue-scripts/glue_bedrock_batch_inference.py \
    --job-name bedrock-batch-inference
```
<!-- python deploy_glue_job.py \
    --script-location s3://aws-glue-assets-687752207838-us-west-2/scripts/glue_bedrock_batch_inference.py \
    --job-name bedrock-batch-inference -->


This will:
- Create an IAM role with necessary permissions
- Create or update the Glue job configuration

## Running the Job

Start the Glue job with required parameters:

```bash
aws glue start-job-run \
    --job-name bedrock-batch-inference \
    --arguments '{
        "--input_path": "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_All_Beauty_0.jsonl",
        "--output_path": "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/meta_All_Beauty_0.jsonl.out",
        "--model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "--rpm": "100",
        "--max_worker" : "10"
    }'
```

### Parameters

- `input_path`: S3 path to input JSONL files
- `output_path`: S3 path for output results
- `model_id`: Bedrock model ID to use (e.g., "anthropic.claude-v2")
- `rpm`: Requests per minute limit (adjust based on your quota)

## Input Format

Input JSONL files should contain records in the following format:
```json
{
    "prompt": "Your prompt text here"
}
```

## Output Format

The job produces JSON files with records in the following format:

For successful requests:
```json
{
    "input": {
        "prompt": "original prompt"
    },
    "output": {
        // Bedrock model response
    },
    "timestamp": "2023-12-20T10:30:00Z",
    "status": "success"
}
```

For failed requests:
```json
{
    "input": {
        "prompt": "original prompt"
    },
    "error": "error message",
    "timestamp": "2023-12-20T10:30:00Z",
    "status": "error"
}
```

## Monitoring and Troubleshooting

1. Monitor job progress in AWS Glue console
2. Check CloudWatch logs for detailed execution logs
3. Use Spark UI for detailed execution metrics
4. Common issues:
   - Insufficient permissions: Check IAM role
   - Rate limiting: Adjust RPM parameter
   - Memory issues: Adjust worker configuration

## Resource Management

The Glue job is configured with:
- 2 workers of type G.1X
- 2880 minute (48 hour) timeout
- Python 3.9 runtime
- Glue version 4.0
- ratelimit package for rate limiting

Adjust these settings in deploy_glue_job.py as needed for your workload.
