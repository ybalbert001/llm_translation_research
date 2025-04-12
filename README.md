# 大语言模型翻译 - Research

## 数据情况

|数据领域|原始来源|数据详情|
|---|---|---|
|游戏|[genshin-impact-ja-zh](https://www.kaggle.com/datasets/toshihikochen/genshin-impact-ja-zh)|原神的公开数据, 存在中文/英文/日文的ground truth|
|电商|[McAuley-Lab/Amazon-Reviews-2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023)|亚马逊商品评论数据中的商品标题, 不存在ground truth, 以Claude Sonnet 3.5翻译结果作为Ground truth|
|混合|[Kaggle_Data](https://www.kaggle.com/datasets/qianhuan/translation/data)|各种类型的数据兼有，存在中文/英文的ground truth|

## 研究范围
1. LLM翻译的问题分析以及总结
2. LLM翻译质量的评估方法
3. 多个模型的翻译能力评估
   1. haiku3
   2. nove-lite
   3. claude sonnet 3.5-v2
   4. claude sonnet 3.7
4. 实验所有的优化手段进行对比
   1. Prompt/Agent-based的优化思路
   2. RAG-based的优化思路
   3. 翻译质量纠察/评估器

## 实施步骤
 - [翻译数据预处理](./1_data_preparation/README.md)
 - [Prompt-based的优化思路](./2_prompt_based_optimization/README.md)
 - [RAG-based的优化思路](./3_retrieval_based_optimization/README.md)
 - [翻译质量评估器](./4_translation_evaluator/README.md)