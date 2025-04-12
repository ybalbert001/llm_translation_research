import boto3
import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
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
                    llm_score = data['modelOutput']['llm_score']
                    sacrebleu = data['modelOutput']['sacrebleu']
                    meteor = data['modelOutput']['meteor']
                    nist = data['modelOutput']['nist']
                    records.append((llm_score, sacrebleu, meteor, nist))
                else:
                    print(f"skip line: {line}")
                    continue

            except (json.JSONDecodeError, KeyError) as e:
                # import traceback
                print(f"Error parsing line: {e}")
                print(f"line: {line}")
                # traceback.print_exc()
                continue
    
    return records

def create_metrics_line_chart(indicator, metric_name, indicator_p50, indicator_mean):
    """
    Create line charts for the four metrics (llm_eval, sacrebleu, meteor, nist) showing both p50 and mean values
    
    Args:
        metrics (dict): Dictionary containing metrics data with p50 and mean values
        file_key (str): S3 key for the file being processed (used for output filename)
    """
    # Extract metric names and values

    # Create figure and axis
    plt.figure(figsize=(10, 6))
    
    # Plot p50 and mean values
    plt.plot(indicator, indicator_p50, marker='o', linestyle='-', linewidth=2, label='p50 (median)')
    plt.plot(indicator, indicator_mean, marker='s', linestyle='--', linewidth=2, label='mean')
    
    # Add labels and title
    plt.xlabel('Metrics')
    plt.ylabel('Values')
    plt.title(f'{metric_name} (p50 vs mean)')
    
    # Add grid and legend
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the chart
    chart_filename = f"{metric_name}_metrics_chart.png"
    plt.savefig(chart_filename)
    print(f"Chart saved to {chart_filename}")
    
    # Close the figure to free memory
    plt.close()

def main():
    """Main function to process translation files and evaluate them"""
    # S3 configuration
    bucket_name = "translation-quality-check-model-sft-20241203"
    prefix = "amazon-review-product-meta-data/retrieval_based_translation/Game/kaggle_genshin/translation_files/evaluations/outputs/"

    try:
        # List files from S3
        print(f"Listing files from s3://{bucket_name}/{prefix}")
        unsorted_file_keys = list_s3_files(bucket_name, prefix)
        file_keys = [unsorted_file_keys[1], unsorted_file_keys[0], unsorted_file_keys[2], unsorted_file_keys[3]]
        
        if not file_keys:
            print("No jsonl.out files found in the specified S3 location.")
            return
        
        print(f"Found {len(file_keys)} jsonl.out files.")

        # Parse files directly from S3
        chart_mean_values = {"llm_eval" : [], "sacrebleu":[], "meteor": [], "nist" : []}
        chart_p50_values = {"llm_eval" : [], "sacrebleu":[], "meteor": [], "nist" : []}
        for file_key in file_keys:
            records = parse_s3_jsonl_files(bucket_name, [file_key])
            
            # Calculate p50 (median) and mean values for each metric
            if records:
                # Convert records to numpy array for easier calculation
                records_array = np.array(records)
                
                # Extract each metric column and filter out None and NaN values
                llm_scores = records_array[:, 0]
                filtered_llm_scores = llm_scores[llm_scores != None]
                sacrebleu_scores = records_array[:, 1]
                filtered_sacrebleu_scores = sacrebleu_scores[sacrebleu_scores != None]
                meteor_scores = records_array[:, 2]
                filtered_meteor_scores = meteor_scores[meteor_scores != None]
                nist_scores = records_array[:, 3]
                filtered_nist_scores = nist_scores[nist_scores != None]
                
                # Calculate median (p50) and mean for each metric

                metrics = {
                    "llm_eval": {
                        "p50": float(np.median(filtered_llm_scores)),
                        "mean": float(np.mean(filtered_llm_scores)),
                        "stat_cnt" : len(filtered_llm_scores)
                    },
                    "sacrebleu": {
                        "p50": float(np.median(filtered_sacrebleu_scores)),
                        "mean": float(np.mean(filtered_sacrebleu_scores)),
                        "stat_cnt" : len(filtered_sacrebleu_scores)
                    },
                    "meteor": {
                        "p50": float(np.median(filtered_meteor_scores)),
                        "mean": float(np.mean(filtered_meteor_scores)),
                        "stat_cnt" : len(filtered_meteor_scores)
                    },
                    "nist": {
                        "p50": float(np.median(filtered_nist_scores)),
                        "mean": float(np.mean(filtered_nist_scores)),
                        "stat_cnt" : len(filtered_nist_scores)
                    }
                }

                chart_mean_values["llm_eval"].append(metrics["llm_eval"]["mean"])
                chart_mean_values["sacrebleu"].append(metrics["sacrebleu"]["mean"])
                chart_mean_values["meteor"].append(metrics["meteor"]["mean"])
                chart_mean_values["nist"].append(metrics["nist"]["mean"])

                chart_p50_values["llm_eval"].append(metrics["llm_eval"]["p50"])
                chart_p50_values["sacrebleu"].append(metrics["sacrebleu"]["p50"])
                chart_p50_values["meteor"].append(metrics["meteor"]["p50"])
                chart_p50_values["nist"].append(metrics["nist"]["p50"])

                md_output = f"""
|metric_name|mean|p50|
|---|---|---|
|llm_eval|{metrics["llm_eval"]["mean"]}|{metrics["llm_eval"]["p50"]}|
|sacrebleu|{metrics["sacrebleu"]["mean"]}|{metrics["sacrebleu"]["p50"]}|
|meteor|{metrics["meteor"]["mean"]}|{metrics["meteor"]["p50"]}|
|nist|{metrics["nist"]["mean"]}|{metrics["nist"]["p50"]}|
"""
                # Print the statistics
                print(f"\nStatistics for {os.path.basename(file_key)}:")
                for metric_name, values in metrics.items():
                    print(f"{metric_name}: median = {values['p50']:.4f}, mean = {values['mean']:.4f}")
                
                # Save statistics to a JSON file
                output_file = os.path.basename(file_key) + "_stat.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f, ensure_ascii=False, indent=2)
                print(f"Statistics saved to {output_file}")

                output_file = os.path.basename(file_key) + "_stat.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(md_output)
                print(f"Statistics saved to {output_file}")
                

            else:
                print(f"No records found for {file_key}, skipping statistics calculation.")
            
        # Create and save line chart
        indicators = [ os.path.basename(file_key).split('.')[0].split("testset_")[1] for file_key in file_keys ] 

        create_metrics_line_chart(indicators, "llm_eval", chart_p50_values["llm_eval"], chart_mean_values["llm_eval"])
        create_metrics_line_chart(indicators, "sacrebleu", chart_p50_values["sacrebleu"], chart_mean_values["sacrebleu"])
        create_metrics_line_chart(indicators, "meteor", chart_p50_values["meteor"], chart_mean_values["meteor"])
        create_metrics_line_chart(indicators, "nist", chart_p50_values["nist"], chart_mean_values["nist"])

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
