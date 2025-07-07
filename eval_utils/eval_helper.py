from collections import defaultdict
from eval_utils.eval_setup import get_chapter_name_from_code, get_concept_distance
from eval_utils.metrics import mean_reciprocal_rank, precision_at_k, recall_at_k


def convert_mimic_codes_to_four_digits(mimic_icd_code):

    mimic_icd_code = mimic_icd_code.strip().replace(" ", "").replace("-", "").replace(".", "").replace(",", "")

    if len(mimic_icd_code) == 1:
        four_digit_standard_code = "000" + str(mimic_icd_code)
    elif len(mimic_icd_code) == 2:
        four_digit_standard_code = "00" + str(mimic_icd_code)
    elif len(mimic_icd_code) == 3:
        four_digit_standard_code = "0" + str(mimic_icd_code)
    elif len(mimic_icd_code) > 4:
        four_digit_standard_code = str(mimic_icd_code)[:4]
    else:
        four_digit_standard_code = str(mimic_icd_code)
    
    standard_code_with_periods = four_digit_standard_code[:2] + "." + four_digit_standard_code[2:3] + "." + four_digit_standard_code[3:]

    return {"four_digit_code": four_digit_standard_code, "code_with_periods": standard_code_with_periods}



def get_completion_statistics(discussion_data):

    num_round_per_window = []
    expert_confidence_levels = []
    last_round_expert_confidence_levels = []

    # get number of rounds
    window_idx_to_num_rounds = defaultdict(int)
    for proposal_instance in discussion_data["discussion"]:
        if "role" in proposal_instance:
            cur_window_idx = int(proposal_instance["admission_window_idx"])
            cur_round_idx = int(proposal_instance["round_idx"])
            window_idx_to_num_rounds[cur_window_idx] = max(window_idx_to_num_rounds[cur_window_idx], cur_round_idx)
    
    for k, v in window_idx_to_num_rounds.items():
        num_round_cur_window = v + 1  # +1 because round_idx starts from 0
        window_idx_to_num_rounds[k] = num_round_cur_window  # +1 because round_idx starts from 0
        # print(type(num_round_cur_window))
        num_round_per_window.append(num_round_cur_window)

    for proposal_instance in discussion_data["discussion"]:
        if "expert" in proposal_instance.keys(): # is not system or leader
            raw_confidence = proposal_instance["response"]["Confidence"]
            try:
                if isinstance(raw_confidence, str):
                    if "%" in raw_confidence:
                        cur_confidence = int(raw_confidence.replace("%", "")) // 10
                    else:
                        cur_confidence = int(float(raw_confidence))
                elif isinstance(raw_confidence, (int, float)):
                    cur_confidence = int(raw_confidence)
                if cur_confidence < 0 or cur_confidence > 10:
                    cur_confidence = 0
            except Exception as e:
                # print(f"Error parsing confidence for proposal instance: {proposal_instance}. Error: {e}")
                cur_confidence = 0

            cur_window_idx = int(proposal_instance["admission_window_idx"])
            cur_round_idx = int(proposal_instance["round_idx"])
            
            expert_confidence_levels.append(cur_confidence)

            if cur_round_idx == window_idx_to_num_rounds[cur_window_idx] - 1:
                last_round_expert_confidence_levels.append(cur_confidence)

    return {
        "num_round_per_window": num_round_per_window,
        "expert_confidence_levels": expert_confidence_levels,
        "last_round_expert_confidence_levels": last_round_expert_confidence_levels
    }


def get_accuracy_statistics(ground_truth_codes_with_periods, predicted_codes_with_periods, ICD_9_CM_graph):
    """
    Calculate accuracy statistics such as precision, recall, and MRR.
    
    Args:
        ground_truth_codes_with_periods (list): List of ground truth ICD codes with periods.
        predicted_codes_with_periods (list): List of predicted ICD codes with periods.
        
    Returns:
        dict: A dictionary containing precision, recall, and MRR.
    """

    min_concept_distance = 8 # max diameter of the ICD-9-CM graph is 8
    for gt_code in ground_truth_codes_with_periods:
        for pred_code in predicted_codes_with_periods:
            success, dist = get_concept_distance(ICD_9_CM_graph, gt_code, pred_code)
            if success:
                min_concept_distance = min(dist, min_concept_distance)

    ground_truth_chapter_names = [get_chapter_name_from_code(code) for code in ground_truth_codes_with_periods]
    predicted_chapter_names = [get_chapter_name_from_code(code) for code in predicted_codes_with_periods]

    ground_truth_first_two_digits = [code[:2] for code in ground_truth_codes_with_periods]
    predicted_first_two_digits = [code[:2] for code in predicted_codes_with_periods]

    ground_truth_three_digits = [code[:3] for code in ground_truth_codes_with_periods]
    predicted_three_digits = [code[:3] for code in predicted_codes_with_periods]

    mrr_chaper_level = mean_reciprocal_rank(ground_truth_chapter_names, predicted_chapter_names)
    mrr_two_digits = mean_reciprocal_rank(ground_truth_first_two_digits, predicted_first_two_digits)
    mrr_three_digits = mean_reciprocal_rank(ground_truth_three_digits, predicted_three_digits)
    mrr_four_digits = mean_reciprocal_rank(ground_truth_codes_with_periods, predicted_codes_with_periods)

    # precision at k
    precision_chapter_level_k2 = precision_at_k(ground_truth_chapter_names, predicted_chapter_names, k=2)
    precision_chapter_level_k5 = precision_at_k(ground_truth_chapter_names, predicted_chapter_names, k=5)
    precision_chapter_level_k10 = precision_at_k(ground_truth_chapter_names, predicted_chapter_names, k=10)

    precision_two_digits_k2 = precision_at_k(ground_truth_first_two_digits, predicted_first_two_digits, k=2)
    precision_two_digits_k5 = precision_at_k(ground_truth_first_two_digits, predicted_first_two_digits, k=5)
    precision_two_digits_k10 = precision_at_k(ground_truth_first_two_digits, predicted_first_two_digits, k=10)

    precision_three_digits_k2 = precision_at_k(ground_truth_three_digits, predicted_three_digits, k=2)
    precision_three_digits_k5 = precision_at_k(ground_truth_three_digits, predicted_three_digits, k=5)
    precision_three_digits_k10 = precision_at_k(ground_truth_three_digits, predicted_three_digits, k=10)

    # recall at k
    recall_chapter_level_k2 = recall_at_k(ground_truth_chapter_names, predicted_chapter_names, k=2)
    recall_chapter_level_k5 = recall_at_k(ground_truth_chapter_names, predicted_chapter_names, k=5)
    recall_chapter_level_k10 = recall_at_k(ground_truth_chapter_names, predicted_chapter_names, k=10)

    recall_two_digits_k2 = recall_at_k(ground_truth_first_two_digits, predicted_first_two_digits, k=2)
    recall_two_digits_k5 = recall_at_k(ground_truth_first_two_digits, predicted_first_two_digits, k=5)
    recall_two_digits_k10 = recall_at_k(ground_truth_first_two_digits, predicted_first_two_digits, k=10)

    recall_three_digits_k2 = recall_at_k(ground_truth_three_digits, predicted_three_digits, k=2)
    recall_three_digits_k5 = recall_at_k(ground_truth_three_digits, predicted_three_digits, k=5)
    recall_three_digits_k10 = recall_at_k(ground_truth_three_digits, predicted_three_digits, k=10)

    return {
        "min_concept_distance": min_concept_distance,
        "mrr_chapter_level": mrr_chaper_level,
        "mrr_two_digits": mrr_two_digits,
        "mrr_three_digits": mrr_three_digits,
        "mrr_four_digits": mrr_four_digits,
        "precision_chapter_level_k2": precision_chapter_level_k2,
        "precision_chapter_level_k5": precision_chapter_level_k5,
        "precision_chapter_level_k10": precision_chapter_level_k10,
        "precision_two_digits_k2": precision_two_digits_k2,
        "precision_two_digits_k5": precision_two_digits_k5,
        "precision_two_digits_k10": precision_two_digits_k10,
        "precision_three_digits_k2": precision_three_digits_k2,
        "precision_three_digits_k5": precision_three_digits_k5,
        "precision_three_digits_k10": precision_three_digits_k10,
        "recall_chapter_level_k2": recall_chapter_level_k2,
        "recall_chapter_level_k5": recall_chapter_level_k5,
        "recall_chapter_level_k10": recall_chapter_level_k10,
        "recall_two_digits_k2": recall_two_digits_k2,
        "recall_two_digits_k5": recall_two_digits_k5,
        "recall_two_digits_k10": recall_two_digits_k10,
        "recall_three_digits_k2": recall_three_digits_k2,
        "recall_three_digits_k5": recall_three_digits_k5,
        "recall_three_digits_k10": recall_three_digits_k10
    }
    


if __name__ == "__main__":

    # print(convert_mimic_codes_to_four_digits("62"))
    # res = get_accuracy_statistics()

    gt = ['96.7.1', '96.0.4', '38.9.3', '38.9.1', '31.4.2', '96.0.7']
    pred = ['87.0.3', '87.3.1', '88.2.2']

    res = get_accuracy_statistics(gt, pred)
    print(res)