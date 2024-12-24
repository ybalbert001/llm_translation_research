### 准备数据

#### 0. 安装依赖包
> pip3 install requirements.txt

#### 1.从Hugging Face上下载数据，并提取对应字段
> 执行extract_hf_amazon_data.py，输出到S3目录 s3://{bucket}/amazon-review-product-meta-data/batch-inference

#### 2.把原始title整理成batch inference的输入prompt jsonl文件
> 执行batch_infer_data_process.py， 输出到S3目录 s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/{model_name}/
>
> For Claude Batch Inference,  batch_inference_input/claude/
> python batch_infer_data_process.py --target-lang zh-cn --model_name claude
> python batch_infer_data_process.py --target-lang ru-ru --model_name claude
>
> For Nova Batch Inference,  batch_inference_input/nova/
> python batch_infer_data_process_nova.py --target-lang ru-ru --model_name nova
> python batch_infer_data_process_nova.py --target-lang zh-cn --model_name nova

#### 3.执行batch_inference, 得到批量运行的结果

> batch_inference 默认的并发job数为20个
> batch_inference 默认的每个job数中最多5w个record

> 输入S3路径
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/{model_name}/

> 输出S3路径 
>	s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/
> 	s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/35-v2/

```bash
# claude 3.5 v2
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

# haiku3
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

> #### 运行nova 的 batch inference
> ##### nova-pro 模型仅仅在us-east-1可用，需要拷贝到us-east-1
```bash
aws s3 cp s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/nova s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova --recursive --source-region us-west-2 --region us-east-1
```

> ##### [注意] nova-pro 不支持stop_sequences 参数; 参考[文档](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)支持的是stopSequences

```bash
# nova-lite
python run_batch_inference.py \
    --region us-east-1 \
    --input_s3_uri_list \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Appliances_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Arts_Crafts_and_Sewing_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Books_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Electronics_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Industrial_and_Scientific_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Kindle_Store_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Software_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Toys_and_Games_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Unknown_0.jsonl \
        s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-input/nova/ru-ru/meta_Video_Games_0.jsonl \
    --output_s3_uri s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaLite/ru-ru/ \
    --model_id amazon.nova-lite-v1:0
```

> #### 运行完毕后，把输出拷贝会us-west-2
```bash
aws s3 cp s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaLite/ru-ru s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/novaLite/ru-ru --recursive --source-region us-east-1 --region us-west-2
```