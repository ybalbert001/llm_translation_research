import boto3
import json
import ast
from typing import Any, List, Dict
from sagemaker_inference import get_predictor, inference

def list_s3_files(bucket: str, prefix: str) -> List[str]:
    """List all files in S3 bucket with given prefix."""
    s3_client = boto3.client('s3')
    files = []
    
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.json'):
                    files.append(obj['Key'])
    
    return files

def read_s3_json(bucket: str, key: str) -> Any:
    """Read JSON file from S3."""
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    return json.loads(content)

def compare_label_prediction(label_msg, prediction_msg):
    """
    label_msg & prediction_msg pattern:
    <think>The translation omits the brand name 'Dinghosen' but uses more appropriate technical terms like '门封圈' and '固定夹'. All key components are translated accurately with proper terminology. The format is maintained with no additional numbering. Numbers and product codes are preserved correctly. No non-Chinese words or abnormal symbols present.</think>, So here are my ratings for each criterion: [4.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    
    获取ratings中的最低分，以及最低分的序号
    """
    ratings_left = label_msg.split("So here are my ratings for each criterion: ")[1]
    ratings_right = prediction_msg.split("So here are my ratings for each criterion: ")[1]
    ratings_left = ast.literal_eval(ratings_left)
    ratings_right = ast.literal_eval(ratings_right)

    # 找出左侧（label）的最低分及其索引
    min_score_left = min(ratings_left)
    min_index_left = ratings_left.index(min_score_left)
    
    # 找出右侧（prediction）的最低分及其索引
    min_score_right = min(ratings_right)
    min_index_right = ratings_right.index(min_score_right)

    return min_score_left, min_index_left, min_score_right, min_index_right

def evaluate_testset(predictor, testset_path):
    """Evaluate test set using the specified SageMaker endpoint."""

    if not testset_path.startswith('s3://'):
        raise RuntimeError(f"invalid testset_path of {testset_path}")
    
    bucket = testset_path.split('/')[2]
    prefix = '/'.join(testset_path.split('/')[3:])
    test_files = list_s3_files(bucket, prefix)

    eval_result = []
    for file_key in test_files:
        print(f"Processing {file_key}")
        
        # Read test data
        json_obj_list = read_s3_json(bucket, file_key)
        
        # Process each example in the test file
        for idx, json_obj in enumerate(json_obj_list):
            if idx > 100:
                continue
            # Prepare messages for the model
            messages = json_obj["messages"]

            c35v2_assistant_reply = messages.pop()
            label = c35v2_assistant_reply["content"]
            try:
                prediction = inference(predictor, messages)
            except Exception as e:
                print(f"Error processing messagess: {messages}", flush=True)
                continue
            # print("-----label-----")
            # print(label)

            # print("-----prediction-----")
            # print(prediction)
            min_score_left, min_index_left, min_score_right, min_index_right = compare_label_prediction(label, prediction)

            eval_data = {
                "file_key" : file_key,
                "label" : label, 
                "label_min_score" : min_score_left,
                "label_minscore_index" : min_index_left,
                "prediction" : prediction,
                "prediction_min_score" : min_score_right,
                "prediction_minscore_index" : min_index_right
            }
            eval_result.append(eval_data)

            if idx % 10 == 0:
                print(f"Processed {idx} examples in {file_key}", flush=True)
        
    with open("eval_details.json", 'w') as outf:
        outf.write(json.dumps(eval_result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Evaluate translation test set using SageMaker endpoint')
    parser.add_argument('--endpoint', type=str, required=True, help='SageMaker endpoint name')
    parser.add_argument('--aws_region', type=str, required=True, help='')
    parser.add_argument('--ak', type=str, required=True, help='')
    parser.add_argument('--sk', type=str, required=True, help='')
    parser.add_argument('--testset_path', type=str, required=True, help='')

    ## usage: 
    ## nohup python evaluate_testset.py --endpoint Qwen2-5-7B-Instruct-2025-02-08-07-14-20-517 --aws_region us-east-1 --ak {ak} --sk {sk} --testset_path s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/dataset/testset &

    args = parser.parse_args()
    model_endpoint = args.endpoint
    aws_region = args.aws_region
    ak = args.ak
    sk = args.sk
    testset_path = args.testset_path

    predictor = get_predictor(
        endpoint_name=model_endpoint,
        aws_region=aws_region,
        access_key=ak,
        secret_key=sk
    )

    evaluate_testset(predictor, testset_path)
