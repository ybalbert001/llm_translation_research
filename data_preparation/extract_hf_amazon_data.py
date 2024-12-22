from datasets import load_dataset
from datasets import config
import os
import csv
import boto3
import io

config.HF_DATASETS_TIMEOUT = 600
config.IN_MEMORY_MAX_SIZE = None

os.environ['HF_HOME'] = './hf_cache'  # 设置缓存目录
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['S3_BUCKET'] = 'translation-quality-check-model-sft-20241203'

# Initialize S3 client
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('S3_BUCKET')  # Get S3 bucket from environment variable

if not S3_BUCKET:
    raise ValueError("S3_BUCKET environment variable must be set")

categories = [ "meta_All_Beauty","meta_Amazon_Fashion","meta_Appliances","meta_Arts_Crafts_and_Sewing","meta_Automotive","meta_Baby_Products","meta_Beauty_and_Personal_Care","meta_Books","meta_CDs_and_Vinyl","meta_Cell_Phones_and_Accessories","meta_Clothing_Shoes_and_Jewelry","meta_Digital_Music","meta_Electronics","meta_Gift_Cards","meta_Grocery_and_Gourmet_Food","meta_Handmade_Products","meta_Health_and_Household","meta_Health_and_Personal_Care","meta_Home_and_Kitchen","meta_Industrial_and_Scientific","meta_Kindle_Store","meta_Magazine_Subscriptions","meta_Movies_and_TV","meta_Musical_Instruments","meta_Office_Products","meta_Patio_Lawn_and_Garden","meta_Pet_Supplies","meta_Software","meta_Sports_and_Outdoors","meta_Subscription_Boxes","meta_Tools_and_Home_Improvement","meta_Toys_and_Games","meta_Unknown","meta_Video_Games" ]
categories = [ "meta_Toys_and_Games"]

for category in categories:

    # 使用streaming模式加载数据，只选择title列
    dataset = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_{category}",
        split="full",
        streaming=True,
        trust_remote_code=True
    ).select_columns(['title'])
    # mirror="https://hf-mirror.com"

    batch_titles = []
    batch_size = 48000
    batch_count = 0
    idx = 0

    # 流式处理数据
    for item in dataset:
        if item["title"]:  # 只处理非空title
            batch_titles.append(item["title"])

            if idx % 1000 == 0:
                print(f"process {idx}")
            idx += 1

            # 当收集够一批数据时，上传到S3
            if len(batch_titles) >= batch_size:
                filename = f'{category}_{batch_count * batch_size}.csv'
                s3_key = f'amazon-review-product-meta-data/batch-inference/{filename}'
                
                # 创建内存中的文件对象
                buffer = io.StringIO()
                writer = csv.writer(buffer)
                for title in batch_titles:
                    writer.writerow([title])
                    
                # 上传到S3
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=buffer.getvalue().encode('utf-8')
                )
                
                print(f'Uploaded {len(batch_titles)} titles to s3://{S3_BUCKET}/{s3_key}')
                buffer.close()
                
                # # 重置批次
                # batch_titles = []
                # batch_count += 1

                # 仅仅保留48000
                break
