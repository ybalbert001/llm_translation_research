1. 将翻译结果映射到Glue Table

```bash
# 删除batch_inference的统计文件
python delete_manifest_files.py
# 构建batch_inference 的结果表， 创建了两张推理结果表分别是  claude_inference_table 和 nova_inference_table
python setup_athena_tables.py --database translation_raw --athena_output s3://translation-quality-check-model-sft-20241203/athena-output/ --s3_bucket translation-quality-check-model-sft-20241203 --s3_prefix amazon-review-product-meta-data/batch-inference-output
```

2. 生成各个模型翻译的对比的jsonl文件（中间结果包含combine_translation表, 可供查询对比)
```bash
python gen_compare_data.py --region us-west-2 --database translation_raw --athena_output s3://translation-quality-check-model-sft-20241203/athena-output/ --s3_bucket translation-quality-check-model-sft-20241203 
```

3. 执行batch_inference
```bash
python ../data_preparation/run_batch_inference.py --input_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference/translation_eval/meta_All_Beauty_0_translation_comparison_llm_eval.jsonl --output_s3_uri s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval/ --model_id anthropic.claude-3-5-sonnet-20241022-v2:0
```

4. 下载推理后的结果
```bash
aws s3 cp s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/batch-inference-output/translation_eval/meta_All_Beauty_0_translation_comparison_llm_eval.jsonl.out ./
```

5. 解析推理结果
```bash
python stat_llm_eval_result.py --input ./meta_All_Beauty_0_translation_comparison_llm_eval.jsonl.out --output ./evaluation_summary.json
```