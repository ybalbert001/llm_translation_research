## 基本思路

### 准备数据

#### 1.从Hugging Face上下载数据，并提取对应字段
> 执行extract_hf_amazon_data.py，输出到本地目录 hf_amazon_product_title

#### 2.把原始title整理成batch inference的输入prompt jsonl文件
> 执行batch_infer_data_process.py， 输出到本地目录 batch_inference_input

#### 3.上传数据到S3桶 
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part1/meta_*.jsonl
> s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/part2/meta_*.jsonl

#### 4.执行batch_inference, 得到批量运行的结果
> batch_inference 默认的并发job数为20个

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
```



