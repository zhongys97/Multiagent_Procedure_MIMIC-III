from eval_utils.eval_one_patient import eval_one_patient
from eval_utils.eval_setup import build_icd9_cm_graph
import os
import re
import json
from collections import defaultdict
from tqdm import tqdm

results_dir = "./results" 
output_json_dir = "./eval_results"




def main():

    configs_dir = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, f))]

    
    ICD_9_CM_graph = build_icd9_cm_graph()

    for config_dir in configs_dir:
        config_str = os.path.basename(config_dir)
        admission_files = [f for f in os.listdir(config_dir) if f.endswith('.json') and 'discussion' in f]
        patient_ids = set()
        for filename in tqdm(admission_files):
            match = re.search(r"_subject_(.*?)_admission", filename)
            if match:
                patient_ids.add(match.group(1))

        patient_ids = list(patient_ids)
        individual_results = []
        individual_errors = {}
        average_results = defaultdict(float)
        
        for patient_id in patient_ids:
            # print("$" * 20)
            try:
                individual_result = eval_one_patient(patient_id, config_dir, ICD_9_CM_graph)
                individual_results.append(individual_result["metrics"])

                # print(individual_result["errors_analysis"])
                for key, value in individual_result["errors_analysis"].items():
                    if key not in individual_errors:
                        individual_errors[key] = 0
                    individual_errors[key] += value

            except Exception as e:
                print(f"Error processing patient {patient_id}: {e}")
                continue

        for result in individual_results:
            for key, value in result.items():
                if isinstance(value, str) or key == "patient_id":
                    continue
                average_results[key] += value

        for key in average_results:
            average_results[key] = round(average_results[key] / len(individual_results), 4)

        sum_errors = sum(individual_errors.values())
        for key in individual_errors:
            individual_errors[key] = round(individual_errors[key] / sum_errors, 4) if sum_errors > 0 else 0.0

        res = {
            "average": average_results,
            "errors_analysis": individual_errors,
            "all_results": individual_results,
        }

        with open(os.path.join(output_json_dir, f"{config_str}.json"), "w") as f:
            json.dump(res, f, indent=4)

if __name__ == "__main__":
    main()
    # Example usage:
    # result = eval_one_patient("123456", "/path/to/results")
    # print(result)