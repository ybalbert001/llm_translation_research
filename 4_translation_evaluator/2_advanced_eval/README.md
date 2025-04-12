1. 针对llm-as-a-judge的数据，生成训练数据

> 云上ec2上运行更加快速。本地运行存在大量的数据读写

```bash
nohup python3 generate_dataset.py --input s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval_cot/c35-v2/*/*/*.jsonl.out --output_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/dataset/ &
```

分别输出训练数据和测试数据到trainset/和testset/目录中

2. balance 训练数据

