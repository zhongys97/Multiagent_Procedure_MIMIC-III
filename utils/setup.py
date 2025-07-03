import os
import json
from openai import OpenAI


MAPPING_PATH = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/icd9_procedure_mapping.json"


with open("./api_keys.json", "r") as f:
    os.environ["OPENAI_API_KEY"] = json.load(f)["openai_api_key"]


chapter_idx_to_pkl_name = {
    "1": "Chapter1_infectious_and_parasitic_diseases.pkl",
    "3": "Chapter3_endocrine,_nutritional_and_metabolic_diseases,_and_immunity_disorders.pkl",
    "4": "Chapter4_diseases_of_the_blood_and_blood-forming_organs.pkl",
    "5": "Chapter5_mental_disorders.pkl",
    "7": "Chapter7_diseases_of_the_circulatory_system.pkl",
    "8": "Chapter8_diseases_of_the_respiratory_system.pkl",
    "9": "Chapter9_diseases_of_the_digestive_system.pkl",
    "10": "Chapter10_diseases_of_the_genitourinary_system.pkl",
    "13": "Chapter13_diseases_of_the_musculoskeletal_system_and_connective_tissue.pkl",
    "15": "Chapter15_certain_conditions_originating_in_the_perinatal_period.pkl",
    "16": "Chapter16_symptoms,_signs,_and_ill-defined_conditions.pkl",
    "17": "Chapter17_injury_and_poisoning.pkl",
    "extra": "Supplemental_external_causes_of_injury_and_supplemental_classification.pkl"
}

with open(MAPPING_PATH, "r") as f:
    procedure_text_to_icd = json.load(f)["procedure_text_to_icd"]


def setup_agents(internal_memory: bool):
    agents = {}
    for chapter_idx in ["1", "3", "4", "5", "7", "8", "9", "10", "13", "15", "16", "17", "extra"]:
        expert_domain_str = " ".join(chapter_idx_to_pkl_name[chapter_idx].split("_")[1:]).replace(".pkl", "")

        if internal_memory:
            agents[chapter_idx] = {
            "expert_idx": chapter_idx,
            "expert_domain_str": expert_domain_str,
            "expert_name": "expert in " + expert_domain_str,
            "agent": OpenAI(),
            "memory": []
        }
        else:
            agents[chapter_idx] = {
                "expert_idx": chapter_idx,
                "expert_domain_str": expert_domain_str,
                "expert_name": "expert in " + expert_domain_str,
                "agent": OpenAI()
            }
    return agents
