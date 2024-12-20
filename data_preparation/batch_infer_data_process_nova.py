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
    
    system_list = [
        {
            "text": "你是一位翻译专家，擅长翻译商品title。"
        }
    ]

    # Configure the inference parameters.
    inf_params = {
        "max_new_tokens": 2048, 
        "top_p": 0.9, 
        "top_k": 20, 
        "temperature": 0.7, 
        "stopSequences" : ['</translation>']
    }

    message_list = [{"role": "user", "content": [{"text": "A camping trip"}]}]

    # Process each row and write to JSONL
    with jsonlines.open(jsonl_path, 'w') as wfd:
        for idx, row in df.iterrows():
            record_id = f"{base_name}_{idx}"
            title = row[0]
            record = {
                "recordId": f"{record_id}", 
                "modelInput": {
                    "schemaVersion": "messages-v1",
                    "system" : system_list,
                    "inferenceConfig": inf_params,
                    "messages": [ 
                        { 
                            "role": "user", 
                            "content": [
                                {
                                    "text": f"请精准的把<src>中的商品Title翻译为zh-cn, 输出到<translation> xml tag中。\n<src>{title}</src>\n" 
                                } 
                            ]
                        },
                        { 
                            "role": "assistant", 
                            "content": [
                                {
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
    inputs = ["./hf_amazon_product_title/meta_All_Beauty_0.csv"]

    for input in inputs:
        csv_files = glob.glob(input)
        # Process each CSV file
        for csv_file in csv_files:
            process_csv_file(csv_file)

if __name__ == '__main__':
    main()
