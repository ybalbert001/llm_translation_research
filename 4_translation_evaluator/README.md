# 翻译评估

### 数据情况
```bash
base_path='s3://amazon-review-product-meta-data/retrieval_based_translation'

# 游戏数据
game_base_path='${base_path}/Game/kaggle_genshin'

# 电商数据

```

### 基础评估方法(1_basic_eval)

- 基于指标的评估
- llm-as-a-judge 利用LLM进行评估

**评估步骤：**

1. 准备评估数据
   1. 处理脚本脚本: [convert_translation_to_eval_input.py](./1_basic_eval/convert_translation_to_eval_input.py)
   2. 数据输入路径: `$game_base_path/translation_files/evaluations/inputs`
2. 构建评估工作流
   1. [translation-eval.yml](./1_basic_eval/translation-eval.yml)
3. 批量运行评估及统计
   1.  通过 [intelligent-bedrock-batch-inference](https://github.com/ybalbert001/intelligent-bedrock-batch-inference) 批量调用dify工作流
   2.  输出路径 `$game_base_path/translation_files/evaluations/output`
   3.  运行统计脚本[stat_on_eval.py](./1_basic_eval/stat_on_eval.py)，生成metric和chart。

### 高级评估方法(2_avdanced_eval)

1. 训练评估模型
2. 构建错误探查模块