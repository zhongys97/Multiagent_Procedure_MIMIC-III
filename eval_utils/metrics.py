def mean_reciprocal_rank(ground_truth, predicted):
    """
    Compute MRR for a single prediction-ground truth pair.
    """
    rr_total = 0
    for item in ground_truth:
        try:
            rank = predicted.index(item) + 1  # 1-based rank
            rr_total += 1 / rank
        except ValueError:
            rr_total += 0  # Item not found
    return rr_total / len(ground_truth) if ground_truth else 0


def precision_at_k(ground_truth, predicted, k):
    """
    Precision@K: proportion of top-k predicted items that are in the ground truth.
    """
    predicted_at_k = predicted[:k]
    correct = sum(1 for item in predicted_at_k if item in ground_truth)
    return correct / k if k > 0 else 0


def recall_at_k(ground_truth, predicted, k):
    """
    Recall@K: proportion of ground truth items that appear in the top-k predicted items.
    """
    predicted_at_k = predicted[:k]
    correct = sum(1 for item in ground_truth if item in predicted_at_k)
    return correct / len(ground_truth) if ground_truth else 0
