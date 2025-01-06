import boto3
import time
from datetime import datetime
import argparse
import json
from botocore.exceptions import ClientError

create_table_sql = """
CREATE EXTERNAL TABLE IF NOT EXISTS combine_translation (
  recordid STRING,
  src STRING,
  translation_a STRING,
  translation_b STRING
)
PARTITIONED BY (language STRING, model_a STRING, model_b STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LOCATION 's3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_combine/';
"""

add_compare_partition_sql_template = """
INSERT INTO combine_translation
WITH nova_results AS (
  SELECT
    regexp_extract(modelinput.messages[1].content[1].text, '<src>(.*?)</src>', 1) AS src,
    REPLACE(modeloutput.output.message.content[1].text, '</translation>', '') AS translation,
    recordid,
    model,
    language
  FROM
    nova_inference_results
  WHERE
    recordid <> '' AND model in ('{model_a}','{model_b}') 
),
claude_results AS (
  SELECT
    regexp_extract(modelinput.messages[1].content[1].text, '<src>(.*?)</src>', 1) AS src,
    modeloutput.content[1].text AS translation,
    recordid,
    model,
    language
  FROM
    claude_inference_results
  WHERE
    recordid <> '' AND model in ('{model_a}', '{model_b}') 
)
SELECT
  recordid,
  src,
  MAX(CASE WHEN model = '{model_a}' THEN translation ELSE NULL END) AS translation_a,
  MAX(CASE WHEN model = '{model_b}' THEN translation ELSE NULL END) AS translation_b,
  language,
  '{model_a}' as model_a,
  '{model_b}' as model_b
FROM
(
SELECT * FROM nova_results
UNION ALL
SELECT * FROM claude_results
) as tmp 
GROUP BY
recordid,
src,
language
"""

query_translation_compare_data_sql_template = """
select recordid, src, translation_a, translation_b, language, model_a, model_b from combine_translation where recordid <> '' and model_a='{model_a}' and model_b='{model_b}'
"""

def execute_query(client, query, database, s3_output):
    """Execute Athena query and wait for completion"""
    try:
        # Start query execution
        response = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': s3_output}
        )
        
        execution_id = response['QueryExecutionId']
        state = 'RUNNING'
        
        # Wait for query to complete
        while state in ['RUNNING', 'QUEUED']:
            time.sleep(5)
            response = client.get_query_execution(QueryExecutionId=execution_id)
            state = response['QueryExecution']['Status']['State']
            
            if state == 'FAILED':
                raise Exception(response['QueryExecution']['Status']['StateChangeReason'])
            elif state == 'SUCCEEDED':
                return execution_id
                
    except ClientError as e:
        raise Exception(f"AWS API error: {str(e)}, SQL:{query}")

def iterate_query_results(client, execution_id):
    """Get results of completed Athena query"""
    try:
      next_token = None

      while True:
          if next_token:
              response = client.get_query_results(QueryExecutionId=execution_id, NextToken=next_token)
          else:
              response = client.get_query_results(QueryExecutionId=execution_id)

          for row in response['ResultSet']['Rows']:
              if row['Data'][0]['VarCharValue'] == 'recordid':
                  continue  # Skip header row'

              if 'VarCharValue' in row['Data'][0] and 'VarCharValue' in row['Data'][1] and 'VarCharValue' in row['Data'][2] and 'VarCharValue' in row['Data'][3]:
                  yield row['Data'][0]['VarCharValue'], row['Data'][1]['VarCharValue'], row['Data'][2]['VarCharValue'], row['Data'][3]['VarCharValue'], row['Data'][4]['VarCharValue'], row['Data'][5]['VarCharValue'], row['Data'][6]['VarCharValue']

          if 'NextToken' not in response:
              break
      
          next_token = response['NextToken']

    except ClientError as e:
        raise Exception(f"Failed to get query results: {str(e)}")
    
def build_eval_batch_inference_json(record_id, src, translation_a, translation_b, language):
    system_prompt = """You are an expert linguist specializing in translation quality assessment. Your task is to evaluate translations produced by different language models from a given source text. Assess each translation based on the following criteria:

  1. Sensitive content should not be refused to translate
  2. No non-target language word appears
  3. No adding irrelevant words
  4. No Spelling, abnormal symbols and grammar errors detected
  5. Quantity, Quantifiers and Units are translated accurately
  6. Format maintained between source and translation. No added numbering/bullet
  7. key words are translated accurately with appropriate word

  """

    prefill="```json"
    user_prompt_part1 = f"""## Source Text
<source>
<content>{src}</content>
</source>

## Translations
<translations target_lang="{language}">
<translation id="1">
<translator>machine</translator>
<content>{translation_a}</content>
</translation>
<translation id="2">
<translator>expert</translator>
<content>{translation_b}</content>
</translation>
</translations>
"""
    user_prompt_part2 = """
## Evaluation Example
```json
[
{ "id": 1, "thought" : "....", scores : [5.0, ...]},
{ "id": 2, "thought" : "....", scores : [5.0, ...]},
]
```

## Notice
1. Please be sure to provide independent evaluations for both translations. 
2. When assessing machine's translation, you may refer to the expert's translation, but do not compare these two in your thought process. 
3. Simply provide objective factual criteria for evaluation in "thought" field.

Please rate each translation in these 7 aspects (0 - 5.0), the "scores" should be a list with a length of 7. """
    user_prompt = user_prompt_part1 + user_prompt_part2
    record = {
        "recordId": f"{record_id}", 
        "modelInput": {
            "anthropic_version": "bedrock-2023-05-31", 
            "max_tokens": 4096,
            "stop_sequences" : ['```'],
            "system" : system_prompt,
            "messages": [ 
                { 
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": user_prompt 
                        } 
                    ]
                },
                { 
                    "role": "assistant", 
                    "content": [
                        {
                            "type": "text", 
                            "text": prefill 
                        } 
                    ]
                }
            ]
        }
    }

    return json.dumps(record, ensure_ascii=False)

def write_results_to_s3(s3_client, results, bucket, key):
    jsonl_content = '\n'.join(results)

    import pdb
    pdb.set_trace()
    # Upload to S3
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=jsonl_content.encode('utf-8'),
            ContentType='application/json'
        )
    except ClientError as e:
        raise Exception(f"Failed to write to S3: {str(e)}")

def main():
    
    date_str = datetime.now().strftime('%Y%m%d%H%M')
    # AWS configuration
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Translation comparison tool')
    parser.add_argument('--region', type=str, default='us-west-2',
                      help='AWS region name')
    parser.add_argument('--database', type=str, default='translation_raw',
                      help='Athena database name')
    parser.add_argument('--athena_output', type=str, 
                      default='s3://translation-quality-check-model-sft-20241203/athena-output/',
                      help='S3 output location for Athena query results')
    parser.add_argument('--s3_bucket', type=str,
                      default='translation-quality-check-model-sft-20241203',
                      help='S3 bucket for final output')
    parser.add_argument('--s3_prefix', type=str,
                  default='amazon-review-product-meta-data/batch-inference-input/translation_eval',
                  help='S3 bucket for final output')
    parser.add_argument('--model_a', type=str,
                  default='novaLite',
                  help='the lower level translation model')
    parser.add_argument('--model_b', type=str,
                  default='c35-v2',
                  help='the higher level translation model')
  
    args = parser.parse_args()

    region = args.region
    database = args.database
    athena_output = args.athena_output
    s3_bucket = args.s3_bucket 
    s3_path = f'amazon-review-product-meta-data/batch-inference-output/translation_combine/{date_str}'  
    s3_eval_path = args.s3_prefix
    model_a = args.model_a
    model_b = args.model_b
    
    # Initialize AWS clients
    athena_client = boto3.client('athena', region_name=region)
    s3_client = boto3.client('s3', region_name=region)

    try:
        # Execute query
        print("Executing Athena query...")
        execute_query(athena_client, create_table_sql, database, athena_output)

        add_compare_partition_sql_instance = add_compare_partition_sql_template.format(model_a=model_a, model_b=model_b)
        execute_query(athena_client, add_compare_partition_sql_instance, database, athena_output)

        query_translation_compare_data_sql_instance = query_translation_compare_data_sql_template.format(model_a=model_a, model_b=model_b)
        execution_id = execute_query(athena_client, query_translation_compare_data_sql_instance, database, athena_output)

        # Get results
        print("Getting query results...")
        json_list = []
        idx = 0
        for record_id, src, translation_a, translation_b, language, model_a, model_b in iterate_query_results(athena_client, execution_id):
            record = build_eval_batch_inference_json(record_id, src, translation_a, translation_b, language)
            json_list.append(record)
            
            if len(json_list) == 48000:
                filename = f"{model_a}-{model_b}-{idx}.jsonl"
                write_results_to_s3(s3_client, json_list, s3_bucket, s3_eval_path+'/'+filename)
                json_list.clear()
                idx += 1
                print(f"Finsh writing jsonl file of {filename}")
        
        # 最后一轮可能没有48000条
        filename = f"{model_a}-{model_b}-{idx}.jsonl"
        write_results_to_s3(s3_client, json_list, s3_bucket, s3_eval_path+'/'+filename)
        json_list.clear()
        idx += 1
        print(f"Finsh writing jsonl file of {filename}")
        print(f"Results written to s3://{s3_bucket}/{s3_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    main()



