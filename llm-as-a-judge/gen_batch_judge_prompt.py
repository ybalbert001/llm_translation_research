import jsonlines
import json
import pandas as pd
import os
import argparse

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

def process_csv_file(csv_path):
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Create output JSONL filename
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    jsonl_path = f"{base_name}_llm_eval.jsonl"
    
    # Process each row and write to JSONL
    with jsonlines.open(jsonl_path, 'w') as wfd:
        for idx, row in df.iterrows():
            record_id = f"{base_name}_{idx}"
            
            source = row[1]
            c35_translation = row[2]
            haiku3_translation = row[3]
            nova_pro_translation = row[4].replace("</translation>", "")
            haiku35_translation = row[5]
            nova_lite_translation = row[6].replace("</translation>", "")
            user_prompt_part1 = f"""## Source Text
<text>
{source}
</text>

## Translations
<translations>
<translation id="1">
{c35_translation}
</translation>
<translation id="2">
{haiku35_translation}
</translation>
<translation id="3">
{haiku3_translation}
</translation>
<translation id="4">
{nova_pro_translation}
</translation>
<translation id="5">
{nova_lite_translation}
</translation>
</translations>
"""
            
            user_prompt_part2 = """
## Evaluation Example
```json
[
{ "id": 1, "thought" : "....", scores : [5.0, ...]},
{ "id": 2, "thought" : "....", scores : [5.0, ...]},
{ "id": 3, "thought" : "....", scores : [5.0, ...]},
{ "id": 4, "thought" : "....", scores : [5.0, ...]},
{ "id": 5, "thought" : "....", scores : [5.0, ...]}
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

            wfd.write(record)

def main():
    parser = argparse.ArgumentParser(description='Generate batch judge prompts from a CSV file.')
    parser.add_argument('csv_path', help='Path to the input CSV file')
    args = parser.parse_args()
    
    # csv 's schema
    # record_id,source,c35_translation,haiku3_translation,nova_pro_translation,haiku35_translation,nova_lite_translation
    process_csv_file(args.csv_path)

if __name__ == '__main__':
    main()
