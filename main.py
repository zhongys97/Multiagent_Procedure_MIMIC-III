from utils.setup import setup_agents, setup_models
from pipeline.discussion import run_by_subject_json
import os
import json

NUM_ROUNDS = 6  # Define the number of rounds for the discussion
END_CONDITION = "consensus"
MODEL = "gpt-4.1-mini"  # gpt-4.1-mini, gpt-4o, claude-3, or medllama
QUERY_LITERATURE = False

RESULT_DIR = "./results"
PATIENT_EHR_DIR = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/patient_procedures_json"  # Path to the patient EHR data
ICD_MAPPING_PATH = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/icd9_procedure_mapping.json"
API_KEYS_JSON_PATH = "./api_keys.json"  # Path to the API keys JSON file
RAG_DATA_DIR = "./MIMIC3_RAG"


def main():
    """
    Main function to run the discussion pipeline.
    """
    config_str = f"{MODEL}_{END_CONDITION}_query_{QUERY_LITERATURE}"
    config_run_dir = os.path.join(RESULT_DIR, config_str)
    if not os.path.exists(config_run_dir):
        os.makedirs(config_run_dir)

    agents = setup_agents(internal_memory=QUERY_LITERATURE)
    model_info = setup_models(model_name=MODEL, api_keys_json_path=API_KEYS_JSON_PATH)

    with open(ICD_MAPPING_PATH, "r") as f:
        procedure_text_to_icd = json.load(f)["procedure_text_to_icd"]

    
    patient_ehr_paths = [os.path.join(PATIENT_EHR_DIR, f) for f in os.listdir(PATIENT_EHR_DIR) if f.endswith('.json')]

    for patient_ehr_path in patient_ehr_paths:
        run_by_subject_json(config_run_dir=config_run_dir,
                            patient_ehr_json_path=patient_ehr_path,
                            agents=agents,
                            model_info=model_info,
                            num_rounds=NUM_ROUNDS,
                            end_condition=END_CONDITION,
                            query_literature=QUERY_LITERATURE,
                            rag_data_dir=RAG_DATA_DIR,
                            procedure_text_to_icd=procedure_text_to_icd)

if __name__ == "__main__":
    main()