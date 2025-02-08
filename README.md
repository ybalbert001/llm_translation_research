# 大语言模型翻译 - Research

## 数据情况
目前数据集局限在商品Title翻译场景，也可以扩展到其他的场景 

1. 原始数据集：

https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main/raw/meta_categories

2. 原文数据(for Batch Inference - jsonl)

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/{model_name}/

3. 译文数据(Batch Inference result - jsonl)

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/nova-lite/

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35-v2/
...

以上数据分别被挂载为athena表
- claude_inference_table
- nova_inference_table
- translation_combine (对比数据表)

4. 翻译质量评估输入数据(novaLite vs c35-v2)

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-input/translation_eval/

5. 翻译质量评估结果数据

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval/

6. 翻译问题分析COT合成数据
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval_cot

## 初步计划
1. 先局限在“英翻中”
2. 先跑出个别品类的训练数据，再做全品类的训练

## 实施步骤
 - [准备翻译数据](./1.data_preparation/README.md)
 - [比较模型翻译质量](./2.llm-as-a-judge/README.md)
 - [准备评估器的训练数据](./3.train_evaluator/README.md)

用sonnet来对haiku的翻译效果做评估，训练一个基于2者比较的sft 翻译检查模型
