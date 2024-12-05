import jsonlines
import json
import pandas as pd
import glob
import os

def process_csv_file(csv_path):
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Create output JSONL filename
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    jsonl_path = f"{base_name}.jsonl"
    
    # Process each row and write to JSONL
    with jsonlines.open(jsonl_path, 'w') as wfd:
        for idx, row in df.iterrows():
            record_id = f"{base_name}_{idx}"
            title = row[0]
            record = {
                "recordId": f"{record_id}", 
                "modelInput": {
                    "anthropic_version": "bedrock-2023-05-31", 
                    "max_tokens": 2048,
                    "stop_sequences" : ['</translation>'],
                    "messages": [ 
                        { 
                            "role": "user", 
                            "content": [
                                {
                                    "type": "text", 
                                    "text": f"你是一位翻译专家，擅长翻译商品title。请精准的把<src>中的商品Title翻译为zh-cn, 输出到<translation> xml tag中。\n<src>{title}</src>\n" 
                                } 
                            ]
                        },
                        { 
                            "role": "assistant", 
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "<translation>" 
                                } 
                            ]
                        }
                    ]
                }
            }

            wfd.write(record)

def main():
    # Find all CSV files with prefix meta_All_Beauty
    inputs = ["meta_Amazon_Fashion_*", "meta_Appliances_*"]

    for input in inputs:
        csv_files = glob.glob(input)
        # Process each CSV file
        for csv_file in csv_files:
            process_csv_file(csv_file)

if __name__ == '__main__':
    main()
