## 数据情况
```bash
base_path='s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/retrieval_based_translation'

# 游戏数据
game_base_path='${base_path}/Game/kaggle_genshin'

# 电商数据

```

## 准备专词数据

数据处理方法： 

1. 数据预处理
   1. 根据原始数据，构建输入数据，具体格式参见`$game_base_path/term_files/inputs`

2. 构建Dify工作流
   1. [Game_Term_Extractor.yml](./1_term_extraction/Game_Term_Extractor.yml)

3. 通过 [intelligent-bedrock-batch-inference](https://github.com/ybalbert001/intelligent-bedrock-batch-inference) 批量调用dify工作流
   1. 输入数据 `$game_base_path/term_files/inputs`
   2. 输出数据 `$game_base_path/term_files/outputs`

4. 利用脚本 [convert_to_dictionary.py ](./1_term_extraction/convert_to_dictionary.py) 把批量运行的数据转换成专词文件
   1. 执行脚本 
      ```
      aws s3 sync s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/retrieval_based_translation/Game/kaggle_genshin/term_files/outputs/ ./ --exclude "*" --include "*.jsonl.out"
      ls */*/*.jsonl.out
      python convert_to_dictionary.py job_0/1744615765/GenshinReadable.jsonl.out job_1/1744643716/GenshinSubtitle.jsonl.out -o genshin_combined_dictionary_threshold_1.json
      ```
   2. 上传到输出路径 `$game_base_path/term_files/extracted_terms`




## 准备样例数据

根据原始数据编写原始数据，

输出路径：`${game_base_path}/example_files/en2zh`

s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/retrieval_based_translation/Game/kaggle_genshin/example_files/zh2en/zh-cn-en-us_readable_testset.txt

## 执行召回优化翻译

1. 数据准备
   1. 下载样例数据中的测试集`aws s3 sync s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/retrieval_based_translation/Game/kaggle_genshin/example_files/zh2en/ ./ --exclude "*" --include "*.txt"`，执行 `python ./3_retrieval_based_optimization/generate_input_data.py` 生成输入数据
   2. 输入数据路径``${game_base_path}/translation_files/inputs`, 其中的所有jsonl数据为输入数据
2. 构建翻译工作流
   1. [Translate_ReSearch_Mihoyo_Genshin.yml](./3_batch_translation/Translate_ReSearch_Mihoyo_Genshin.yml)
3. 通过 [intelligent-bedrock-batch-inference](https://github.com/ybalbert001/intelligent-bedrock-batch-inference) 批量调用dify工作流，生成不同优化方式的翻译结果
   1. 输出数据路径 `${game_base_path}/translation_files/outputs`
