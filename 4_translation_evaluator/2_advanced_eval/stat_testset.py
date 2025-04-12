import json
import numpy as np
from sklearn.metrics import classification_report

y_true = []
y_pred = []

# label_7 意味着没问题
with open("eval_details.json", 'r') as input_f:
    result_list = json.loads(input_f.read())
    for item in result_list:
        label_idx = item["label_minscore_index"]
        label_val = label_idx if item["label_min_score"] < 4 else 7
        pred_idx = item["prediction_minscore_index"]
        pred_val = pred_idx if item["prediction_min_score"] < 4 else 7
        y_true.append(label_val)
        y_pred.append(pred_val)

report = classification_report(y_true, y_pred)
print("\nClassification Report:\n", report)