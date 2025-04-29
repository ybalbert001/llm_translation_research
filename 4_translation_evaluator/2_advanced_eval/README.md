# 1.训练数据构造

> 【注意】云上ec2上运行更加快速。本地运行存在大量的数据读写

> 【Input数据情况】
> novaLite 与 claude3.5-v2的翻译数据 [数据位置说明](../../1_data_preparation/README.md) 

> 【数据处理的时间估计】
> **处理速度**     rpm=150 rph=150*60=9000
> **处理数据量**   SELECT count(1) FROM "AwsDataCatalog"."translation_raw"."combine_translation"  481109
> **处理时间**     53h

### 1.1 数据版本 - v1 
> claude3.5作为llm-as-a-judge， 针对NovaLite与Claude3.5-v2生成翻译质量评估作为训练数据的原料

- 数据预处理
```
nohup python3 process_dataset.py --input s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval_cot/c35-v2/*/*/*.jsonl.out --output_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1 &

```

- 数据合成
```
# 遍历S3目录中的所有文件，对于数据量不满足100条的进行数据合成
python3 synthesize_data.py --input_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/origin/ --min_samples 100 --max_workers 10
```

- 拆分训练集/测试集
```python
python3 gen_train_test_set.py --origin_dataset s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_a/origin/ --synthetic_dataset s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_a/synethic/ --output_train s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_a/trainset/ --output_test s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_a/testset/ --test_ratio 0.1

python3 gen_train_test_set.py --origin_dataset s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_b/origin/ --synthetic_dataset s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_b/synethic/ --output_train s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_b/trainset/ --output_test s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/model_b/testset/ --test_ratio 0.1
```

### 1.2 数据版本 - v2
> claude3.7作为llm-as-a-judge， 针对NovaLite与Claude3.5-v2生成翻译质量评估作为训练数据的原料


```
# 1. 针对llm-as-a-judge的数据，生成训练数据
# 
# > 云上ec2上运行更加快速。本地运行存在大量的数据读写
# 
# nohup python3 generate_dataset.py --input s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/# translation_eval_cot/c35-v2/*/*/*.jsonl.out --output_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/dataset/ &
# 
# 分别输出训练数据和测试数据到trainset/和testset/目录中
# 
# 2. balance 训练数据
```
