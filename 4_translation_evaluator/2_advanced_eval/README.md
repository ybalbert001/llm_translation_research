# 1.训练数据构造

> 【注意】云上ec2上运行更加快速。本地运行存在大量的数据读写

> 【Input数据情况】
> novaLite 与 claude3.5-v2的翻译数据 [数据位置说明](../../1_data_preparation/README.md) 

> 【数据处理的时间估计】
> **处理速度**     rpm=150 rph=150*60=9000
> **处理数据量**   SELECT count(1) FROM "AwsDataCatalog"."translation_raw"."combine_translation"  481109
> **处理时间**     53h

> 【目标模型】
>  simple_model: 比较简单的翻译规则问题检测
>  complex_model: 复杂的翻译用词问题检测

### 1.1 数据版本 - v1 
> claude3.5作为llm-as-a-judge， 针对NovaLite与Claude3.5-v2生成翻译质量评估作为训练数据的原料

- 数据预处理 (按照simple_model和complex_model分别输出)
```
cd model_data_process
nohup python3 process_dataset.py --input s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval_cot/c35-v2/*/*/*.jsonl.out --output_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1 &

```

- 数据合成
> 仅针对simple_model，complex_model数据量要求较高，合成不了那么多
```
# 遍历S3目录中的所有文件，对于数据量不满足100条的进行数据合成
cd model_data_process
python3 synthesize_data.py --input_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/origin/ --target_count 200 --max_workers 10

python3 synthesize_data.py --input_dir s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v2/simple_model/origin/ --target_count 200 --max_workers 10
```

- 拆分训练集/测试集
```python
# 拆分数据For simple_model
cd model_data_process
python3 gen_simple_model_train_test_set.py --synthetic_dataset s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/synethic/ --output_bucket translation-quality-check-model-sft-20241203 --output_dir amazon-review-product-meta-data/finetune_based_translation/v1/simple_model

# 拆分数据For complex_model
python3 gen_complex_model_train_test_set.py --origin_dataset s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/complex_model/origin/ --output_bucket translation-quality-check-model-sft-20241203 --output_dir amazon-review-product-meta-data/finetune_based_translation/v1/complex_model
```

# 2.模型训练
数据路径(trainset):
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/openai_trainset/category-0.json
...
s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/openai_trainset/category-5.json

> 由于Model hub仅仅可以访问sagemaker所在的bucket，需要拷贝上面数据到sagemaker所在桶
```
aws cp s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/openai_trainset/ s3://sagemaker-us-east-1-687752207838/translation_sft_dataset/openai_trainset/ --recursive
```

**model hub 数据定义,[参考](https://github.com/xiehust/LLaMA-Factory/tree/main/data)**
```
{
  "category-0": {
    "file_name": "category-0.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  },
  "category-1": {
    "file_name": "category-1.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  },
  "category-2": {
    "file_name": "category-2.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  },
  "category-3": {
    "file_name": "category-3.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  },
  "category-4": {
    "file_name": "category-4.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  },
  "category-5": {
    "file_name": "category-5.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "system_tag": "system"
    }
  }
}

```
