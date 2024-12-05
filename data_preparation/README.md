## 基本思路
用sonnet来对haiku的翻译效果做评估，训练一个基于2者比较的sft 翻译检查模型

## 数据集
局限在商品Title翻译场景，也可以复制到其他的场景
https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main/raw/meta_categories

## 初步计划
1. 先局限在“英翻中”
2. 先跑出个别品类的训练数据
3. 统计分析2个模型之间 一致的部分，不一致的部分，以及差异的部分，得到最终的训练集🏋️


## 实施步骤

### 准备数据

#### 1.从Hugging Face上下载数据，并提取对应字段
> 执行extract_hf_amazon_data.py，输出到本地目录 hf_amazon_product_title

#### 2.把原始title整理成batch inference的输入prompt jsonl文件
> 执行batch_infer_data_process.py， 输出到本地目录 batch_inference_input

#### 3.上传数据到S3桶 
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part1/meta_*.jsonl
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_*.jsonl

#### 4.执行batch_inference, 得到批量运行的结果
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/35-v2/


