import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import regexp_extract, when, col, lit, max as spark_max
from datetime import datetime
import json

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
<text>
{src}
</text>

## Translations (target_lang: {language})
<translations>
<translation id="1">
{translation_a}
</translation>
<translation id="2">
{translation_b}
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

def get_compare_data_from_s3(glueContext, database):
    # Create dynamic frames for nova and claude results
    nova_dyf = glueContext.create_dynamic_frame.from_catalog(
        database=database,
        table_name="nova_inference_results"
    )
    
    claude_dyf = glueContext.create_dynamic_frame.from_catalog(
        database=database,
        table_name="claude_inference_results"
    )
    
    # Convert to Spark DataFrames for more complex operations
    nova_df = nova_dyf.toDF()
    claude_df = claude_dyf.toDF()
    
    # Extract required fields from nova results
    nova_results = nova_df.filter(col("recordid") != "") \
        .filter(col("model") == "novaLite") \
        .select(
            regexp_extract(col("modelinput.messages")[1]["content"][1]["text"], "<src>(.*?)</src>", 1).alias("src"),
            regexp_extract(col("modeloutput.output.message.content")[1]["text"], "(.*?)</translation>", 1).alias("translation"),
            col("recordid"),
            col("model"),
            col("language")
        )
    
    # Extract required fields from claude results
    claude_results = claude_df.filter(col("recordid") != "") \
        .filter(col("model") == "haiku3") \
        .select(
            regexp_extract(col("modelinput.messages")[1]["content"][1]["text"], "<src>(.*?)</src>", 1).alias("src"),
            col("modeloutput.content")[1]["text"].alias("translation"),
            col("recordid"),
            col("model"),
            col("language")
        )
    
    # Union the results
    combined_results = nova_results.union(claude_results)
    
    # Pivot the results to get translations side by side
    compare_data = combined_results.groupBy("recordid", "src", "language") \
        .agg(
            spark_max(when(col("model") == "haiku3", col("translation"))).alias("translation_a"),
            spark_max(when(col("model") == "novaLite", col("translation"))).alias("translation_b")
        ) \
        .withColumn("model_a", lit("haiku3")) \
        .withColumn("model_b", lit("novaLite"))
    
    return compare_data

def process_and_write_results(compare_data, s3_bucket, s3_prefix):
    date_str = datetime.now().strftime('%Y%m%d%H%M')
    
    # Convert DataFrame to RDD for processing
    def process_row(row):
        return build_eval_batch_inference_json(
            row.recordid,
            row.src,
            row.translation_a,
            row.translation_b,
            row.language
        )
    
    # Process rows and write in batches
    jsonl_rdd = compare_data.rdd.map(process_row)
    
    # Write results in batches of 48000
    batch_size = 48000
    total_count = jsonl_rdd.count()
    num_batches = (total_count + batch_size - 1) // batch_size
    
    for i in range(num_batches):
        batch = jsonl_rdd.zipWithIndex() \
            .filter(lambda x: i * batch_size <= x[1] < (i + 1) * batch_size) \
            .map(lambda x: x[0])
        
        filename = f"haiku3-novaLite-{i}.jsonl"
        s3_path = f"s3://{s3_bucket}/{s3_prefix}/{filename}"
        
        # Convert batch to DataFrame and write to S3
        batch_df = batch.toDF()
        batch_df.coalesce(1).write.mode("overwrite").text(s3_path)

def main():
    # Get job parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'database',
        's3_bucket',
        's3_prefix'
    ])
    
    # Initialize Spark context
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    # Get comparison data
    compare_data = get_compare_data_from_s3(glueContext, args['database'])
    
    # Process and write results
    process_and_write_results(
        compare_data,
        args['s3_bucket'],
        args['s3_prefix']
    )
    
    # Commit the job
    job.commit()

if __name__ == '__main__':
    main()
