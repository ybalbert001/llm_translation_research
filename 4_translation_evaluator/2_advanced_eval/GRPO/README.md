## 安装依赖
```
python3.12 -m pip install boto3 pandas pyarrow tqdm --break-system-packages
```

## 构建GRPO数据

```
python construct_dataset.py --input "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v2/simple_model/trainset/*.json" --output "s3://sagemaker-us-east-1-687752207838/translation_sft_dataset/openai_trainset_simple_model/v2/grpo_dataset/trainset.parquet"

python construct_dataset.py --input "s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v2/simple_model/testset/*.json" --output "s3://sagemaker-us-east-1-687752207838/translation_sft_dataset/openai_trainset_simple_model/v2/grpo_dataset/testset.parquet"
```