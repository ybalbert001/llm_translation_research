# 准备数据

**安装依赖包**

```bash
conda activate translate
pip3 install -r requirements.txt
```

### 1. 下载原始数据 
**1.1 准备电商数据**

从Hugging Face上下载数据，并提取对应字段

执行extract_hf_amazon_data.py，输出到S3目录：
```
s3://{bucket}/amazon-review-product-meta-data/batch-inference
```

**1.2 准备游戏数据和混合数据**

从Kaggle上下载数据

- 安装Kaggle API
    ```
    pip install kaggle
    ```
- 获取API凭证
    登录Kaggle账户
    点击右上角头像 -> "Account"
    滚动到"API"部分，点击"Create New API Token"
    这会下载kaggle.json文件
    ```
    mkdir -p ~/.kaggle
    cp kaggle.json ~/.kaggle/
    chmod 600 ~/.kaggle/kaggle.json
    ```
- 下载数据
    ```
    kaggle datasets download -d qianhuan/translation
    kaggle datasets download -d toshihikochen/genshin-impact-ja-zh
    unzip translation.zip
    unzip genshin-impact-ja-zh.zip
    ```
- 处理原始数据并上传到S3
    ```
    python preprocess_kaggle_data.py --input_dir ../dataset/genshin-impact-ja-zh --output_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/kaggle/game
    aws s3 cp  ../dataset/translation2019zh/translation2019zh_train.json s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/kaggle/mixed/
    aws s3 cp  ../dataset/translation2019zh/translation2019zh_valid.json s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/kaggle/mixed/
    ```

**1.3 准备游戏专词数据**

```
wget https://dataset.genshin-dictionary.com/words.json
```

### 2. 通过batch_inference准备电商翻译数据

**2.1 把原始title整理成batch inference的输入prompt jsonl文件**

执行batch_infer_data_process.py，输出到S3目录：
```
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/{model_name}/
```

For Claude Batch Inference (batch_inference_input/claude/)
```bash
python batch_infer_data_process.py --target-lang zh-cn --model_name claude
python batch_infer_data_process.py --target-lang ru-ru --model_name claude
```

For Nova Batch Inference (batch_inference_input/nova/)
```bash
python batch_infer_data_process.py --target-lang ru-ru --model_name nova
python batch_infer_data_process.py --target-lang zh-cn --model_name nova
```

**2.2 执行batch_inference, 得到批量运行的结果**

> batch_inference 默认的并发job数为20个
> batch_inference 默认的每个job数中最多5w个record

输入S3路径：
```
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/{model_name}/
```

输出S3路径：
```
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/35-v2/
```

执行下面脚本
```bash
python run_batch_inference.py \
    --region us-west-2 \
    --input_s3_uri_list \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_All_Beauty_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Amazon_Fashion_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Appliances_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Arts_Crafts_and_Sewing_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Automotive_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Baby_Products_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Beauty_and_Personal_Care_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Books_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_CDs_and_Vinyl_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Cell_Phones_and_Accessories_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Clothing_Shoes_and_Jewelry_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Digital_Music_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Electronics_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Grocery_and_Gourmet_Food_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Handmade_Products_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Health_and_Household_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Health_and_Personal_Care_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Home_and_Kitchen_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Industrial_and_Scientific_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Kindle_Store_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Movies_and_TV_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Musical_Instruments_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Office_Products_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Patio_Lawn_and_Garden_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Pet_Supplies_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Software_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Sports_and_Outdoors_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Tools_and_Home_Improvement_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Toys_and_Games_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Unknown_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Video_Games_0.jsonl \
    --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/ru-ru/ \
    --model_id anthropic.claude-3-5-sonnet-20241022-v2:0
```

```bash
python run_batch_inference.py \
    --region us-west-2 \
    --input_s3_uri_list \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Appliances_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Arts_Crafts_and_Sewing_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Books_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Electronics_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Industrial_and_Scientific_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Kindle_Store_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Software_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Toys_and_Games_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Unknown_0.jsonl \
        s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/ru-ru/meta_Video_Games_0.jsonl \
    --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ru-ru/ \
    --model_id anthropic.claude-3-haiku-20240307-v1:0
```

**2.3 注意事项 （Nova Batch Inference）**

1. nova-pro 模型仅仅在us-east-1可用，需要拷贝到us-east-1
```bash
aws s3 cp s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/nova s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova --recursive --source-region us-west-2 --region us-east-1
```

2. [注意] nova-pro 不支持stop_sequences 参数; 参考[文档](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)支持的是stopSequences

```bash
# nova 
# model_id = [ 'amazon.nova-micro-v1:0', 'amazon.nova-pro-v1:0']
python run_batch_inference.py \
    --region us-east-1 \
    --input_s3_uri_list \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Appliances_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Arts_Crafts_and_Sewing_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Books_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Electronics_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Industrial_and_Scientific_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Kindle_Store_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Software_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Toys_and_Games_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Unknown_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/zh-cn/meta_Video_Games_0.jsonl \
    --output_s3_uri s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaPro/zh-cn/ \
    --model_id amazon.nova-pro-v1:0
```

运行完毕后，把输出拷贝回us-west-2
```bash
aws s3 sync s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaMicro/zh-cn s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/novaMicro/zh-cn  --source-region us-east-1 --region us-west-2

aws s3 sync s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaLite/zh-cn s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/novaLite/zh-cn --source-region us-east-1 --region us-west-2

aws s3 sync s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaPro/zh-cn s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/novaPro/zh-cn --source-region us-east-1 --region us-west-2
```



### 3. 通过Glue Job批量推理 (batch inference 由于资源原因不可用)

> 如果bedrock batch_inference 由于资源问题难以获得结果，那么可以采用[intelligent-bedrock-batch-inference](https://github.com/ybalbert001/intelligent-bedrock-batch-inference)以onDemand的方式运行批量推理

**参数解释**

- input_s3_uri_list: 为以","分隔的s3路径列表
- output_s3_uri: 为s3路径目录
- rpm: 为运行的速率，需要根据账户的quota进行设置
- ak/sk/region: 可以供你选择其他的账户进行推理，如果不填写，默认使用本账户进行推理

```bash
aws glue start-job-run \
    --job-name intelligent-bedrock-batch-inference \
    --arguments '{
        "--input_s3_uri_list": "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/claude/zh-cn/meta_Appliances_0.jsonl",
        "--output_s3_uri": "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35-v2/zh-cn/",
        "--model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "--rpm": "50",
        "--max_worker" : "10",
        "--ak" : "{ak}",
        "--sk" : "{sk}",
        "--region" : "{region}"
    }'
```

更多用法参见 [README_zh.md](https://github.com/ybalbert001/intelligent-bedrock-batch-inference/blob/main/README_zh.md)

> 以上数据分别被挂载为athena表
> - claude_inference_table
> - nova_inference_table
> - translation_combine (对比数据表)

