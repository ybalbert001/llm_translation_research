# 大语言模型翻译 - Research

## 研究方向
1. Agent-based LLM Translation
2. Example Retrieve LLM Translation
3. Term Mapping Retrieve LLM Translation
4. SFT Translation Evaluation LLM 

## 数据集
局限在商品Title翻译场景，也可以复制到其他的场景
https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main/raw/meta_categories

## 初步计划
1. 先局限在“英翻中”
2. 先跑出个别品类的训练数据，再做全品类的训练

## 实施步骤
 - [准备数据](./data_preparation/README.md)
 - [比较模型翻译质量](./llm-as-a-judge/README.md)


用sonnet来对haiku的翻译效果做评估，训练一个基于2者比较的sft 翻译检查模型
