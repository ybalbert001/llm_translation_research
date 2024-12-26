import boto3
import json
import argparse

def create_iam_role():
    """Create IAM role for Glue job with necessary permissions"""
    iam = boto3.client('iam')
    
    # Create role
    trust_relationship = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "glue.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam.create_role(
            RoleName='GlueBedockBatchInferenceRole',
            AssumeRolePolicyDocument=json.dumps(trust_relationship)
        )
        
        # Attach necessary policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy in policies:
            iam.attach_role_policy(
                RoleName='GlueBedockBatchInferenceRole',
                PolicyArn=policy
            )
        
        return response['Role']['Arn']
    except iam.exceptions.EntityAlreadyExistsException:
        return iam.get_role(RoleName='GlueBedockBatchInferenceRole')['Role']['Arn']

def create_glue_job(role_arn, script_location, job_name='bedrock-batch-inference'):
    """Create or update Glue job"""
    glue = boto3.client('glue')
    
    job_config = {
        'Name': job_name,
        'Role': role_arn,
        'Command': {
            'Name': 'pythonshell',
            'ScriptLocation': script_location,
            'PythonVersion': '3'
        },
        'DefaultArguments': {
            '--enable-metrics': '',
            '--enable-continuous-cloudwatch-log': 'true',
            '--additional-python-modules': 'boto3>=1.35.87,botocore>=1.35.87'
        },
        'MaxRetries': 0,
        'Timeout': 2880,
        'GlueVersion': '3.0',
        'MaxCapacity': 1.0
    }
    
    try:
        glue.create_job(**job_config)
        print(f"Created new Glue job: {job_name}")
    except glue.exceptions.AlreadyExistsException:
        glue.update_job(JobName=job_name, JobUpdate=job_config)
        print(f"Updated existing Glue job: {job_name}")

def main():
    parser = argparse.ArgumentParser(description='Deploy Glue job for Bedrock batch inference')
    parser.add_argument('--script-location', required=True, help='S3 location of the Glue script')
    parser.add_argument('--job-name', default='bedrock-batch-inference', help='Name for the Glue job')
    
    args = parser.parse_args()
    
    # Create IAM role
    print("Creating/updating IAM role...")
    role_arn = create_iam_role()
    print(f"Role ARN: {role_arn}")
    
    # Create Glue job
    print("Creating/updating Glue job...")
    create_glue_job(role_arn, args.script_location, args.job_name)
    print("Done!")

if __name__ == '__main__':
    main()
