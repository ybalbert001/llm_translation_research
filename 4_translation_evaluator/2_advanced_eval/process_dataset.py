import json
import argparse
import boto3
import os
import math
import glob
from botocore.config import Config
from collections import defaultdict
import xml.etree.ElementTree as ET

from utils import get_score_category

def extract_source_and_translations(json_str):
    """Extract source text and translations from the input."""
    try:
        data = json.loads(json_str)
        messages = data["modelInput"]["messages"][0]["content"]
        
        source_text = None
        translations = {}
        
        # Parse the text content to extract source and translations
        for item in messages:
            if item["type"] == "text":
                text = item["text"]
                if "Source Text" in text:
                    # Extract source text between <text> tags
                    start = text.find("<source>\n<content>") + len("<source>\n<content>")
                    end = text.find("</content>\n</source>")
                    source_text = text[start:end].strip()
                
                if "<translations" in text:
                    # Extract translations
                    trans_start = text.find("<translations")
                    trans_end = text.find("</translations>") + len("</translations>")
                    xml_string = text[trans_start:trans_end]
                    
                    # 解析 XML 字符串
                    root = ET.fromstring(xml_string)

                    # 提取所有 content 元素的文本
                    contents = [elem.text for elem in root.findall('.//content')]

                    # 打印提取的内容
                    for idx, content in enumerate(contents):
                        translations[idx] = content
        
        return source_text, translations
    except Exception as e:
        print(f"Error extracting source and translations: {str(e)}")
        return None, None

def parse_line_scores(json_str):
    """Parse a single line of JSON and extract scores and thoughts for each translation."""
    try:
        data = json.loads(json_str)
        # Get the text content from modelOutput
        content = data["modelOutput"]["content"][0]["text"]
        record_id = data["recordId"]
        
        # Remove any leading/trailing whitespace and 'json' markers
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        # Parse the JSON array from the content
        evaluations = json.loads(content)
        
        # Extract scores and thoughts for each translation
        translation_data = {}
        for eval in evaluations:
            translation_id = str(eval["id"])  # Convert id to string for consistency
            translation_data[translation_id] = {
                "scores": eval["scores"],
                "thought": eval["thought"]
            }
        
        return record_id, translation_data
    except Exception as e:
        print(f"Error parsing scores: {str(e)}")
        print(f"Content that failed to parse: {content if 'content' in locals() else 'content not available'}")
        return None

def list_s3_files(s3_path):
    """List all S3 files matching the wildcard pattern."""
    s3 = boto3.client('s3')
    bucket = s3_path.split('/')[2]
    prefix = '/'.join(s3_path.split('/')[3:])
    
    # Convert glob pattern to prefix and filter
    # Remove trailing wildcard components from prefix
    clean_prefix = '/'.join([p for p in prefix.split('*')[0].split('/') if p])
    
    files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=clean_prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.jsonl.out'):  # Filter by file extension
                    full_path = f's3://{bucket}/{key}'
                    # Use glob pattern matching
                    if glob.fnmatch.fnmatch(full_path, s3_path):
                        files.append(full_path)
    
    return files

def process_file(file_path):
    """Process the .jsonl file and collect all information."""
    all_data = []
    error_count = 0
    success_count = 0
    total_lines = 0
    
    lines = []
    try:
        # Parse S3 path
        if file_path.startswith('s3://'):
            bucket = file_path.split('/')[2]
            key = '/'.join(file_path.split('/')[3:])

            config = Config(
                retries = {'max_attempts': 10},
                connect_timeout=5,
                read_timeout=360
            )

            s3 = boto3.client('s3', config=config)
            obj = s3.get_object(Bucket=bucket, Key=key)
            lines = obj['Body'].read().decode('utf-8').splitlines()
        else:
            with open(file_path, 'r') as f:
                lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return all_data
            
    for line_num, line in enumerate(lines, 1):
        total_lines += 1
        try:
            # Parse the line
            source_text, translations = extract_source_and_translations(line.strip())
            record_id, translation_data = parse_line_scores(line.strip())
            
            if translation_data:
                # Collect scores for statistics

                details_1 = {
                    "translation" : translations[0],
                    "scores" : translation_data["1"]["scores"],
                    "thought" : translation_data["1"]["thought"]
                }
                
                details_2 = {
                    "translation" : translations[1],
                    "scores" : translation_data["2"]["scores"],
                    "thought" : translation_data["2"]["thought"]
                }

                # Create simplified entry
                entry = {
                    "record_id" : record_id,
                    "source": source_text,
                    "translations": [details_1, details_2]
                }
                all_data.append(entry)
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"Error processing line {line_num}: {line}")
            continue
    
    print(f"\nProcessing Summary:")
    print(f"Total lines processed: {total_lines}")
    print(f"Successfully processed: {success_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Success rate: {(success_count/total_lines)*100:.2f}%\n")
    
    return all_data

def main():
    parser = argparse.ArgumentParser(description='Process LLM evaluation results and generate statistics.')
    parser.add_argument('--input', '-i', required=True,
                      help='Input JSONL file path (local or s3://) containing LLM evaluation results')
    parser.add_argument('--output_dir', '-o', default='.',
                      help='Output directory for statistics files (local or s3://)')

    args = parser.parse_args()
    
    print(f"Processing input path: {args.input}")
    
    # Handle wildcard paths
    if args.input.startswith('s3://') and ('*' in args.input):
        input_files = list_s3_files(args.input)
        print(f"Found {len(input_files)} files matching the pattern")
    else:
        input_files = [args.input]
    
    # Process all matching files
    all_data = []
    for input_file in input_files:
        print(f"\nProcessing file: {input_file}")
        file_data = process_file(input_file)
        all_data.extend(file_data)

    system_prompt= """You are an expert linguist specializing in translation quality assessment. Your task is to evaluate the translation produced by translation model. Assess the translation based on the following criteria:

  1. Sensitive content should not be refused to translate
  2. No non-target language word appears
  3. No adding irrelevant words
  4. No Spelling, abnormal symbols and grammar errors detected
  5. Quantity, Quantifiers and Units are translated accurately
  6. Format maintained between source and translation. No added numbering/bullet
  7. key words are translated accurately with appropriate word"""
    
    user_prompt_template = """Here is the source text in <src> tag and also its translation from an translator in <translation> tag. 
<src>
{src}
</src>

<translation>
{translation_by_machine}
</translation>

Please analyze the translation quality, and finally give the opinion, put your opinion in <opinion> xml tag."""
    assistant_prompt_tempalte = """<think>{thought}</think>, So here are my ratings for each criterion: {scores}"""

    dataset = {"simple_model": {}, "complex_model": {}}
    for data in all_data:
        record_id = data["record_id"]
        record_category = '_'.join(record_id.split('_')[1:-2])
        source = data["source"]
        translations =  data["translations"]
        for record in translations:
            if "translation" not in record:
                continue
            if record["translation"] is None or record["translation"].lower() == 'none':
                continue
            user_prompt = user_prompt_template.format(src=source, translation_by_machine=record["translation"])
            scores = record["scores"]
            cate_id, min_score = get_score_category(scores)
            thought = record["thought"]

            # assistant_prompt = assistant_prompt_tempalte.format(thought=thought, scores=scores)
            # train_record = {
            #     "messages": [
            #         {
            #             "role": "system",
            #             "content": system_prompt
            #         },
            #         {
            #             "role": "user",
            #             "content": user_prompt
            #         },
            #         {
            #             "role": "assistant",
            #             "content": assistant_prompt
            #         }
            #     ]
            # }

            real_existed_records = {
                "source" : data["source"],
                "translation" : record["translation"],
                "thought" : record["thought"],
                "scores" : scores
            }

            key = "{}-cate-{}-score-{}".format(record_category, cate_id, min_score)

            if cate_id in [0,1,2,3,4,5]:
                if key not in dataset["simple_model"]:
                    dataset["simple_model"][key] = []
                dataset["simple_model"][key].append(real_existed_records)
            elif cate_id in [6]:
                if key not in dataset["complex_model"]:
                    dataset["complex_model"][key] = []
                dataset["complex_model"][key].append(real_existed_records)
            
    # Save simplified JSON output
    output_dir = args.output_dir
    if output_dir.startswith('s3://'):
        s3 = boto3.client('s3')
        bucket = output_dir.split('/')[2]
        prefix = '/'.join(output_dir.split('/')[3:])

        for filename, records in dataset["simple_model"].items():
            records_cnt = len(records)
            obj_key = f"{prefix}/simple_model/origin/{filename}-{records_cnt}.json"
            s3.put_object(
                Bucket=bucket,
                Key=obj_key,
                Body=json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8')
            )

            print(f"\ndata has been saved to s3://{bucket}/{obj_key}")
        
        for filename, records in dataset["complex_model"].items():
            records_cnt = len(records)
            obj_key = f"{prefix}/complex_model/origin/{filename}-{records_cnt}.json"
            
            s3.put_object(
                Bucket=bucket,
                Key=obj_key,
                Body=json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8')
            )
        
            print(f"\ndata has been saved to s3://{bucket}/{obj_key}")
    else:
        print(f"Only S3 path accepted..")

if __name__ == "__main__":
    import sys
    print("Received arguments:", sys.argv)
    main()
