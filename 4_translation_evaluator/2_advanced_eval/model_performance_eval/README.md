## 评估方法
```
python calc_metric.py --testset_path s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v1/simple_model/testset/

python calc_metric.py --testset_path s3://translation-quality-check-model-sft-20241203/amazon-review-product-meta-data/finetune_based_translation/v2/simple_model/testset/
```

## V1 
Metrics for category-0.json:
precision: 0.7641509433962265, recall: 0.8804347826086957, MAE: 0.5567567567567567

Confusion Matrix:
[[68 25]
 [11 81]]

Metrics for category-1.json:
precision: 0.9533333333333334, recall: 0.8461538461538461, MAE: 0.5059171597633136

Confusion Matrix:
[[162   7]
 [ 26 143]]

Metrics for category-2.json:
precision: 0.8953488372093024, recall: 0.719626168224299, MAE: 0.7149532710280374
 
Confusion Matrix:
[[98  9]
 [30 77]]


Metrics for category-3.json:   
precision: 0.8333333333333334, recall: 0.46153846153846156, MAE: 1.3153846153846154 

Confusion Matrix:  
[[59  6] 
[35 30]]

Metrics for category-4.json:  
precision: 0.8095238095238095, recall: 0.5862068965517241, MAE: 0.7586206896551724 

Confusion Matrix:
[[25  4] 
[12 17]]

Metrics for category-5.json:  
precision: 0.875, recall: 0.65625, MAE: 0.984375 

Confusion Matrix:
[[29  3]
 [11 21]]

### 整体效果
Overall Metrics: 
precision: 0.8723404255319149, recall: 0.7469635627530364, MAE: 0.7128412537917088 

Confusion Matrix:[[441  54] 
 [125 369]]