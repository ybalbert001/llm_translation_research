import math

def get_score_category(scores):
    min_score = 5
    cate_id = 6
    for cur_cate_id, score in enumerate(scores):
        if score < min_score:
            min_score = score
            cate_id = cur_cate_id
    
    return cate_id, math.floor(min_score)