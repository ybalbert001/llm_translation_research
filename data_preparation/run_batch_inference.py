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

    # 美东需要换这个 amazon-product-title-batch-translate-east-role
    if region == 'us-east-1':
        role_arn = "arn:aws:iam::687752207838:role/service-role/amazon-product-title-batch-translate-east-role"
    elif region == 'us-west-2':
        role_arn = "arn:aws:iam::687752207838:role/service-role/amazon-product-title-batch-translate-role"

    response=bedrock_client.create_model_invocation_job(
        roleArn=role_arn,
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

def get_active_jobs_count(jobs_status):
    """Count number of active jobs (not in terminal states)"""
    terminal_states = {'Completed', 'PartiallyCompleted', 'Failed', 'Stopped', 'Expired'}
    return sum(1 for status in jobs_status.values() if status not in terminal_states)

def parse_args():
    parser = argparse.ArgumentParser(description='Create multiple batch inference jobs with rate limiting')
    parser.add_argument('--region', 
                        default='us-west-2',
                        help='AWS region')
    parser.add_argument('--input_s3_uri_list',
                        nargs='+',
                        required=True,
                        help='List of input S3 URIs')
    
    parser.add_argument('--output_s3_uri',
                        default='s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/',
                        help='Output S3 URI')
    
    parser.add_argument('--model_id',
                        default='anthropic.claude-3-5-sonnet-20240620-v1:0',
                        help='Model ID')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    
    # Track all jobs and their status functions
    jobs = {}  # {job_arn: (get_status_func, stop_func)}
    jobs_status = {}  # {job_arn: status}
    
    # Process each input URI
    for i, input_uri in enumerate(args.input_s3_uri_list):
        # Wait if we have too many active jobs
        while get_active_jobs_count(jobs_status) >= 5:
            print(f"Active jobs limit reached (5). Waiting for 1 minute...")
            time.sleep(60)
            
            # Update status of all jobs
            for job_arn, (get_status, _) in jobs.items():
                jobs_status[job_arn] = get_status(job_arn)
                print(f"Job {job_arn}: {jobs_status[job_arn]}")
        
        # Create new job
        output_uri = f"{args.output_s3_uri.rstrip('/')}/job_{i}/"
        job_arn, get_status_func, stop_func = create_job(
            region=args.region,
            input_s3_uri=input_uri,
            output_s3_uri=output_uri,
            model_id=args.model_id
        )
        
        # Track the new job
        jobs[job_arn] = (get_status_func, stop_func)
        jobs_status[job_arn] = "Submitted"
        
        print(f"Created job {job_arn} for input {input_uri}")
    
    # Wait for all jobs to complete
    while get_active_jobs_count(jobs_status) > 0:
        print("\nChecking job statuses...")
        for job_arn, (get_status, _) in jobs.items():
            jobs_status[job_arn] = get_status(job_arn)
            print(f"Job {job_arn}: {jobs_status[job_arn]}")
        
        if get_active_jobs_count(jobs_status) > 0:
            print("Waiting 1 minute before next status check...")
            time.sleep(60)
    
    print("\nAll jobs completed!")
    for job_arn, status in jobs_status.items():
        print(f"Job {job_arn}: {status}")
