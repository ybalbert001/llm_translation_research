import boto3
import time
import sys
import argparse

sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', buffering=1)

# All possible status:
# Submitted
# Validating
# Scheduled
# Expired
# InProgress
# Completed
# PartiallyCompleted
# Failed
# Stopped
# Stopping

def create_job(region, input_s3_uri, output_s3_uri, model_id):
    bedrock_client = boto3.client(service_name="bedrock", region_name=region)

    inputDataConfig=({
        "s3InputDataConfig": {
            "s3Uri": input_s3_uri
        }
    })

    outputDataConfig=({
        "s3OutputDataConfig": {
            "s3Uri": output_s3_uri
        }
    })

    response=bedrock_client.create_model_invocation_job(
        roleArn="arn:aws:iam::687752207838:role/service-role/amazon-product-title-batch-translate-role",
        modelId=model_id,
        jobName=f"my-batch-job-{region}-{time.time()}",
        inputDataConfig=inputDataConfig,
        outputDataConfig=outputDataConfig
    )

    jobArn = response.get('jobArn')
    print(f"jobArn: {jobArn}")

    def get_status_func(job_arn):
        status = bedrock_client.get_model_invocation_job(jobIdentifier=job_arn)['status']
        return status

    def stop_job_func(job_arn):
        bedrock_client.stop_model_invocation_job(jobIdentifier=job_arn)

    return jobArn, get_status_func, stop_job_func

def parse_args():
    parser = argparse.ArgumentParser(description='Create a job with specified parameters')
    parser.add_argument('--region', 
                        default='us-west-2',
                        help='AWS region')
    parser.add_argument('--input_s3_uri',
                        default='s3://687752207838-23-12-19-08-04-10-bucket/feishushengnuo/data.jsonl',
                        help='Input S3 URI')
    
    parser.add_argument('--output_s3_uri',
                        default='s3://687752207838-23-12-19-08-04-10-bucket/feishushengnuo_output/',
                        help='Output S3 URI')
    
    parser.add_argument('--model_id',
                        default='anthropic.claude-3-5-sonnet-20240620-v1:0',
                        help='Model ID')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    
    job_arn_1 = create_job(
        region=args.region,
        input_s3_uri=args.input_s3_uri,
        output_s3_uri=args.output_s3_uri,
        model_id=args.model_id
    )
