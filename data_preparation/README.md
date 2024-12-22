### 准备数据

#### 1.从Hugging Face上下载数据，并提取对应字段
> 执行extract_hf_amazon_data.py，输出到S3目录 s3://{bucket}/amazon-review-product-meta-data/batch-inference

#### 2.把原始title整理成batch inference的输入prompt jsonl文件
> 执行batch_infer_data_process.py， 输出到本地目录 
>
> For Claude Batch Inference,  batch_inference_input/claude/
>
> For Nova Batch Inference,  batch_inference_input/nova/

#### 3.上传数据到S3桶 
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part1/meta*.jsonl
>
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/nova/meta*.jsonl

#### 4.执行batch_inference, 得到批量运行的结果

> batch_inference 默认的并发job数为20个
> batch_inference 默认的每个job数中最多5w个record

> 输出S3路径 
>	s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/
> 	s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/35-v2/

```bash
# claude 3.5 v2
python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Amazon_Fashion_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/ --model_id anthropic.claude-3-5-sonnet-20241022-v2:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Amazon_Fashion_48000.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/ --model_id anthropic.claude-3-5-sonnet-20241022-v2:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Amazon_Fashion_96000.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/ --model_id anthropic.claude-3-5-sonnet-20241022-v2:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Appliances_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/ --model_id anthropic.claude-3-5-sonnet-20241022-v2:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Appliances_48000.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/c35/ --model_id anthropic.claude-3-5-sonnet-20241022-v2:0

# haiku3
python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Amazon_Fashion_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ --model_id anthropic.claude-3-haiku-20240307-v1:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Amazon_Fashion_48000.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ --model_id anthropic.claude-3-haiku-20240307-v1:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Amazon_Fashion_96000.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ --model_id anthropic.claude-3-haiku-20240307-v1:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Appliances_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ --model_id anthropic.claude-3-haiku-20240307-v1:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_Appliances_48000.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku3/ --model_id anthropic.claude-3-haiku-20240307-v1:0

python run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part1/meta_All_Beauty_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/haiku35/ --model_id anthropic.claude-3-5-haiku-20241022-v1:0

```

> nova-pro 模型仅仅在us-east-1可用，需要跑完后同步到 us-west-2
> 美东需要换这个 amazon-product-title-batch-translate-east-role
> nova-pro 不支持stop_sequences 参数; 参考[文档](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)支持的是stopSequences

```
#nova
python run_batch_inference.py  --region us-east-1 --input_s3_uri s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference/meta_All_Beauty_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaPro/ --model_id amazon.nova-pro-v1:0

python run_batch_inference.py  --region us-east-1 --input_s3_uri s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference/meta_All_Beauty_0.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaLite/ --model_id amazon.nova-lite-v1:0

aws s3 cp s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaPro/5ptd7yqswnty/meta_All_Beauty_0.jsonl.out s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/nova-pro/ --source-region us-east-1 --region us-west-2

aws s3 cp s3://translation-quality-check-model-sft-20241203-east-1/amazon-review-product-meta-data/batch-inference-output/novaLite/kizqbl5qw7y6/meta_All_Beauty_0.jsonl.out s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/nova-lite/ --source-region us-east-1 --region us-west-2

```

