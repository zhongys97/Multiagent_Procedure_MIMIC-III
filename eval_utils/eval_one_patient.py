import json
import os
from eval_utils.eval_helper import convert_mimic_codes_to_four_digits, get_completion_statistics, get_accuracy_statistics
from eval_utils.eval_setup import build_icd9_cm_graph, get_concept_distance
from ast import literal_eval
from collections import defaultdict



perf_metric_keys = [
    "mrr_chapter_level",
    "mrr_two_digits",
    "precision_chapter_level_k2",
    "precision_chapter_level_k5",
    "precision_chapter_level_k10",
    "precision_two_digits_k2",
    "precision_two_digits_k5",
    "precision_two_digits_k10",
    "recall_chapter_level_k2",
    "recall_chapter_level_k5",
    "recall_chapter_level_k10",
    "recall_two_digits_k2",
    "recall_two_digits_k5",
    "recall_two_digits_k10"
]

def eval_one_patient(patient_id: str, result_config_dir: str, ICD_9_CM_graph) -> dict:

    if "consensus" in result_config_dir:
        config = "consensus"
    elif "leader" in result_config_dir:
        config = "leader"
    elif "alone" in result_config_dir:
        config = "alone"

    patient_jsons = [f for f in os.listdir(result_config_dir) if patient_id in f and "discussion" in f and f.endswith('.json')]

    bool_decision_per_admission = []
    num_round_per_window = []
    expert_confidence_levels = []
    last_round_expert_confidence_levels = []
    json_parse_error = 0
    result_not_list_error = 0
    code_alphabet_error = 0
    code_numeric_but_madeup = 0
    other_errors = 0
    
    perf_metrics = defaultdict(list)

    for patient_json in patient_jsons:

        with open(os.path.join(result_config_dir, patient_json), 'r') as f:
            discussion_data = json.load(f)

        gender = discussion_data["gender"]
        ethnicity = discussion_data["ethnicity"]
        language = discussion_data["language"]
        insurance = discussion_data["insurance_type"]

        ground_truth = discussion_data["ground_truth_procedures_icd9"]


        try:
            predicted = discussion_data["final_discussion_procedures_icd9"]
        except Exception as e:
            json_parse_error += 1

        try:
            if config == "leader":
                predicted = discussion_data["final_discussion_procedures_icd9"]

            elif config in ["consensus", "alone"]:
                if len(discussion_data["final_discussion_procedures_icd9"]) == 0:
                    predicted = []
                else:
                    predicted = literal_eval(discussion_data["final_discussion_procedures_icd9"][0])
        except Exception as e:
            # print(f"Error parsing predicted codes for patient {patient_id}: {e}")
            result_not_list_error += 1

        try:
            predicted_cleaned = []
            if isinstance(predicted, list):
                for code in predicted:
                    code = str(code)
                    if len(code) == 0:
                        continue
                    code = "".join(c for c in code)
                    if len(predicted_cleaned) > 0:
                        if code == predicted_cleaned[-1]:
                            continue
                    predicted_cleaned.append(code)
            else:
                predicted_cleaned = [str(predicted)]
        except Exception as e:
            other_errors += 1
            print("Error cleaning prediction code", e)
            print(predicted)

        try:

            ground_truth_codes_with_periods = [convert_mimic_codes_to_four_digits(code)["code_with_periods"] for code in ground_truth]
            predicted_codes_with_periods = [convert_mimic_codes_to_four_digits(code)["code_with_periods"] for code in predicted_cleaned]
            bool_decision_per_admission.append(True if len(predicted_codes_with_periods) > 0 else False)
        except Exception as e:
            other_errors += 1
            print(f"Error converting codes for patient {patient_id}: {e}")

        try:
            completion_statistics = get_completion_statistics(discussion_data)
            num_round_per_window += completion_statistics["num_round_per_window"] # extend the list
            expert_confidence_levels += completion_statistics["expert_confidence_levels"]
            last_round_expert_confidence_levels += completion_statistics["last_round_expert_confidence_levels"]
        except Exception as e:
            other_errors += 1
            print(f"Error processing completion for patient {patient_id}: {e}")

        try:
            accuracy_statistics, pred_codes_contain_alphabet, pred_codes_are_numeric_but_madeup = get_accuracy_statistics(ground_truth_codes_with_periods, predicted_codes_with_periods, ICD_9_CM_graph)
            if pred_codes_contain_alphabet:
                code_alphabet_error += 1
            if pred_codes_are_numeric_but_madeup:
                code_numeric_but_madeup += 1
            
            for key in perf_metric_keys:
                perf_metrics[key].append(accuracy_statistics[key])
            perf_metrics["min_concept_distance"].append(accuracy_statistics["min_concept_distance"])
        except Exception as e:
            other_errors += 1
            print(f"Error calculating accuracy statistics for patient {patient_id}: {e}")
    
    try:
        avg_perf_metrics = {key: sum(perf_metrics[key]) / len(perf_metrics[key]) for key in perf_metric_keys} 

        patient_metrics = {
            "average_completion": sum(bool_decision_per_admission) / len(bool_decision_per_admission),
            "average_num_round": sum(num_round_per_window) / len(num_round_per_window),
            "average_expert_confidence": sum(expert_confidence_levels) / len(expert_confidence_levels) if expert_confidence_levels else 0,
            "average_last_round_expert_confidence": sum(last_round_expert_confidence_levels) / len(last_round_expert_confidence_levels) if last_round_expert_confidence_levels else 0,
            "min_concept_distance": min(perf_metrics["min_concept_distance"]) if perf_metrics["min_concept_distance"] else 8
        }

        
        # for perf_metric in perf_metric_keys:
        #     patient_metrics[perf_metric + "_raw"] = avg_perf_metrics[perf_metric]
        #     patient_metrics[ perf_metric + "_normalized"] = avg_perf_metrics[perf_metric] * patient_metrics["average_completion"]

        for perf_metric in perf_metric_keys:
            patient_metrics[perf_metric] = avg_perf_metrics[perf_metric]


        for k, v in patient_metrics.items():
            patient_metrics[k] = round(v, 4)
            

    except Exception as e:
        print(f"Error aggregating metrics for patient {patient_id}: {e}")
    
    errors_analysis = {
        "json_parse_error": json_parse_error,
        "result_not_list_error": result_not_list_error,
        "code_alphabet_error": code_alphabet_error,
        "code_numeric_but_madeup": code_numeric_but_madeup,
        "other_errors": other_errors
    }

    metrics = {
        "patient_id": int(patient_id),
        "gender": gender,
        "ethnicity": ethnicity,
        "language": language,
        "insurance": insurance,
        **patient_metrics
    }

    return {"metrics": metrics, "errors_analysis": errors_analysis}

if __name__ == "__main__":

    # Build the ICD-9-CM graph
    G = build_icd9_cm_graph()
    res = eval_one_patient(patient_id, result_config_dir, G)

    for k, v in res.items():
        print(f"{k}: {v}")
