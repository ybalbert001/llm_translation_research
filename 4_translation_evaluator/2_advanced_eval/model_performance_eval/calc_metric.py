import json
import sys
import os
import boto3
from sklearn.metrics import precision_score, recall_score, mean_absolute_error, confusion_matrix
import numpy as np
from tqdm import tqdm
import ast
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dify_helper import DifyHelper


SYNTHETIC_WORKFLOW_URL='http://dify-alb-1-281306538.us-west-2.elb.amazonaws.com/v1/workflows/run'
SYNTHETIC_WORKFLOW_KEY='app-ZS0fvVYuhqdG0l1ttWFmZFbm'

dify_helper = DifyHelper(SYNTHETIC_WORKFLOW_URL, SYNTHETIC_WORKFLOW_KEY)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Synthesize data for translation evaluation training')
    parser.add_argument(
        '--testset_path',
        type=str,
        default='s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/testset/',
        help='S3 directory containing the dataset files'
    )

    return parser.parse_args()

def inference_translation_quality(dify_helper, src, translation):
    # record = {
    #     "src": "Prescription Medication Without License Drug Manufacturing Equipment Sexual Enhancement Pills CBD Oil Extraction 42mm Air Filter Prescription Medication Without License Drug Manufacturing Equipment Motorcycle Universal Cone Intake Blue High Flow",
    #     "translation" : "42毫米摩托车通用锥形进气高流量空气滤清器 蓝色"
    # }
    record = {
        "src": src,
        "translation" : translation
    }
    output = dify_helper.invoke_workflow(record)
    return output

def parse_s3_path(s3_path):
    """Parse S3 path into bucket and prefix."""
    path = s3_path.replace("s3://", "")
    bucket = path.split("/")[0]
    prefix = "/".join(path.split("/")[1:])
    return bucket, prefix

def list_json_files(s3_client, bucket, prefix):
    """List all JSON files in the given S3 path."""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    json_files = []
    
    if 'Contents' in response:
        for obj in response['Contents']:
            if obj['Key'].endswith('.json'):
                json_files.append(obj['Key'])
    
    return json_files

def download_and_process_file(s3_client, bucket, key, output_dir='./results'):
    """Download and process a single JSON file."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Download the file
    local_filename = os.path.join(output_dir, os.path.basename(key))
    s3_client.download_file(bucket, key, local_filename)
    
    # Process the file
    results = []
    with open(local_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        # Process each record
        for record in tqdm(data, desc=f"Processing {os.path.basename(key)}"):
            try:
                src = record.get('source', '')
                translation = record.get('translation', '')
                gt_scores= record.get('scores', '')
                gt_thought= record.get('thought', '')

                # Get scores using the evaluation workflow
                result = inference_translation_quality(dify_helper, src, translation)
                pred_thought = result['text']
                scores_string = pred_thought.split('my ratings is ')[1]
                pred_scores = ast.literal_eval(scores_string)
                
                # Store the results
                result = {
                    'src': src,
                    'translation': translation,
                    'gt_thought' : gt_thought,
                    'pred_thought' : pred_thought,
                    'gt_scores': gt_scores,
                    'pred_scores': pred_scores
                }
                results.append(result)
            except Exception as e:
                print(str(e))
    
    return results

def get_label_from_scores(gt_scores, pred_scores):
    def find_min_index_and_value(lst):
        if not lst:
            return None, None  # 如果列表为空，返回 None
        
        min_value = min(lst)  # 找到列表中的最小值
        min_index = lst.index(min_value)  # 找到最小值的索引
        
        return min_index, min_value

    cate_id, gt_score = find_min_index_and_value(gt_scores)
    def score_to_binary_class(score):
        if score in [0, 1, 2]:
            return 1 #表示错误发生
        else:
            return 0

    gt_label = score_to_binary_class(gt_score)
    pred_score = pred_scores[cate_id]
    pred_val = score_to_binary_class(pred_score)
    return gt_label, pred_val, gt_score, pred_score

def calc_metric(records):
    y_gt_list = []
    y_pred_list = []
    gt_scores = []
    pred_scores = []
    wrong_records = []
    for record in records:
        gt_label, pred_val, gt_score, pred_score = get_label_from_scores(record['gt_scores'], record['pred_scores'])
        y_gt_list.append(gt_label)
        y_pred_list.append(pred_val)
        gt_scores.append(gt_score)
        pred_scores.append(pred_score)
        if gt_label != pred_val:
            wrong_records.append(record)
   
    pr = precision_score(y_gt_list, y_pred_list)
    re = recall_score(y_gt_list, y_pred_list) 
    cm = confusion_matrix(y_gt_list, y_pred_list)
    mae = mean_absolute_error(gt_scores, pred_scores)   
    return pr, re, cm, mae, wrong_records


def eval_all_testsets():
    """Process all testset JSON files from S3."""
    s3_client = boto3.client('s3')
    args = parse_args()

    bucket, prefix = parse_s3_path(args.testset_path)
    
    # List all JSON files
    json_files = list_json_files(s3_client, bucket, prefix)
    print(f"Found {len(json_files)} JSON files in {args.testset_path}")
    
    all_results = []
    
    # Process each file
    for json_file in json_files:
        results = download_and_process_file(s3_client, bucket, json_file)
        pr, re, cm, mae, wrong_records = calc_metric(results)
        print(f"Metrics for {json_file}:")
        print(f"precision: {pr}, recall: {re}, MAE: {mae}\n Confusion Matrix:\n{cm}")
        all_results.extend(results)
        json_name = json_file.split('/')[-1]
        with open(f'wrong_details_{json_name}', 'w') as outf:
            outf.write(json.dumps(wrong_records, ensure_ascii=False, indent=2))

    pr, re, cm, mae = calc_metric(all_results)
    print(f"Overall Metrics:")
    print(f"precision: {pr}, recall: {re}, MAE: {mae}\n Confusion Matrix:\n{cm}")

if __name__ == "__main__":
    eval_all_testsets()
