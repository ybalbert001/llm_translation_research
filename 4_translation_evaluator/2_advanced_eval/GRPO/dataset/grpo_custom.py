import re
import ast
from typing import Dict, List

def format_reward(predict: str) -> float:
    # pattern = re.compile(r"<think>(.*?)</think>, my rating is (.+)", re.DOTALL)
    # format_match = re.fullmatch(pattern, predict)
    # return 1.0 if format_match else 0.0
    return 1.0

def accuracy_reward(predict: str, ground_truth: str) -> float:
    # predict_scores = ast.literal_eval(predict.split("my rating is ")[-1])
    # ground_truth_scores = ast.literal_eval(ground_truth.split("my rating is ")[-1])
    
    # gt_score = min(ground_truth_scores)
    # gt_cate_id = ground_truth_scores.index(min(ground_truth_scores))
    # pred_score = predict_scores[gt_cate_id]
    reward = 0.0

    # if (gt_score <=2.0 and pred_score <=2.0) or (gt_score >= 3.0 and pred_score >= 3.0):
    #     reward = 1.0
    # else:
    #     reward = 1 - abs(gt_score-pred_score) / 5
        
    return reward

def compute_score(predicts: List[str], ground_truths: List[str], format_weight: float = 0.1) -> List[Dict[str, float]]:
    scores = []
    for predict, ground_truth in zip(predicts, ground_truths):
        format_score = format_reward(predict)
        accuracy_score = accuracy_reward(predict, ground_truth)
        scores.append(
            {
                "overall": (1 - format_weight) * accuracy_score + format_weight * format_score,
                "format": format_score,
                "accuracy": accuracy_score,
            }
        )

    return scores

if __name__ == "__main__":
	predicts = ["<think>hello</think>, my rating is [1,1,1,1,1]", "<think>hello</think>, my rating is [1,1,1,1,1]"]
	ground_truths = ["<think>hello</think>, my rating is [1,1,1,1,1]", "<think>hello</think>, my rating is [1,1,1,1,1]"]

	scores = compute_score(predicts, ground_truths)
	print(scores)