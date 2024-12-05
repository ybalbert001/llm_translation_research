# 大语言模型翻译 - Research

## 基本思路
用sonnet来对haiku的翻译效果做评估，训练一个基于2者比较的sft 翻译检查模型

## 数据集
局限在商品Title翻译场景，也可以复制到其他的场景
https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main/raw/meta_categories

## 初步计划
1. 先局限在“英翻中”
2. 先跑出个别品类的训练数据
3. 统计分析2个模型之间 一致的部分，不一致的部分，以及差异的部分，得到最终的训练集🏋️

## 实施步骤

 - [准备数据](./data_preparation/README.md)
