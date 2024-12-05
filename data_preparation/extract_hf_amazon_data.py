from datasets import load_dataset
from datasets import config
import os
import csv
import math

config.HF_DATASETS_TIMEOUT = 600
config.IN_MEMORY_MAX_SIZE = None

os.environ['HF_HOME'] = './hf_cache'  # 设置缓存目录
os.environ['HF_HUB_OFFLINE'] = '1'

categories = [ "meta_All_Beauty","meta_Amazon_Fashion","meta_Appliances","meta_Arts_Crafts_and_Sewing","meta_Automotive","meta_Baby_Products","meta_Beauty_and_Personal_Care","meta_Books","meta_CDs_and_Vinyl","meta_Cell_Phones_and_Accessories","meta_Clothing_Shoes_and_Jewelry","meta_Digital_Music","meta_Electronics","meta_Gift_Cards","meta_Grocery_and_Gourmet_Food","meta_Handmade_Products","meta_Health_and_Household","meta_Health_and_Personal_Care","meta_Home_and_Kitchen","meta_Industrial_and_Scientific","meta_Kindle_Store","meta_Magazine_Subscriptions","meta_Movies_and_TV","meta_Musical_Instruments","meta_Office_Products","meta_Patio_Lawn_and_Garden","meta_Pet_Supplies","meta_Software","meta_Sports_and_Outdoors","meta_Subscription_Boxes","meta_Tools_and_Home_Improvement","meta_Toys_and_Games","meta_Unknown","meta_Video_Games" ]

for category in categories[1:5]:

    dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_{category}", split="full", trust_remote_code=True)

    titles = [item["title"] for item in dataset if len(item["title"]) > 0]

    # 计算需要多少个文件
    batch_size = 48000
    num_batches = math.ceil(len(titles) / batch_size)

    # 按批次写入文件
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, len(titles))
        batch_titles = titles[start_idx:end_idx]
        
        # 生成包含起始索引的文件名
        filename = f'{category}_{start_idx}.csv'
        
        # 写入当前批次数据
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for item in batch_titles:
                writer.writerow([item])
        
        print(f'Written {len(batch_titles)} titles to {filename}')
