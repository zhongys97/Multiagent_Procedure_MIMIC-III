import os
import json
from openai import OpenAI
from anthropic import Anthropic



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


def setup_agents(internal_memory: bool):
    agents = {}
    for chapter_idx in ["1", "3", "4", "5", "7", "8", "9", "10", "13", "15", "16", "17", "extra"]:
        expert_domain_str = " ".join(chapter_idx_to_pkl_name[chapter_idx].split("_")[1:]).replace(".pkl", "")

        if internal_memory:
            agents[chapter_idx] = {
            "expert_idx": chapter_idx,
            "expert_domain_str": expert_domain_str,
            "expert_name": "expert in " + expert_domain_str,
            "memory": []
        }
        else:
            agents[chapter_idx] = {
                "expert_idx": chapter_idx,
                "expert_domain_str": expert_domain_str,
                "expert_name": "expert in " + expert_domain_str,
            }
    return agents


def setup_models(model_name: str, api_keys_json_path="./api_keys.json"):
    """
    Setup the model based on the model name.
    """

    with open("./api_keys.json", "r") as f:
        data = json.load(f)
        os.environ["OPENAI_API_KEY"] = data["openai_api_key"]
        os.environ["HF_HOME"] = os.path.expanduser(data["hugging_face_home_path"])
        os.environ["HUGGINGFACE_HUB_TOKEN"] = data["huggingface_key"]
        os.environ["ANTHROPIC_API_KEY"] = data["claude_api_key"]

    if "gpt" in model_name:
        return {
            "model_name": model_name,
            "model_instance": OpenAI(),
        }
    elif model_name == "medllama":
        from transformers import AutoTokenizer, AutoModelForCausalLM

        token = os.environ["HUGGINGFACE_HUB_TOKEN"]

        tokenizer = AutoTokenizer.from_pretrained("Henrychur/MMed-Llama-3-8B", token=token)
        model = AutoModelForCausalLM.from_pretrained("Henrychur/MMed-Llama-3-8B", torch_dtype="bfloat16", token=token, device_map="auto")
        return {
            "model_name": model_name,
            "model_instance": model,
            "tokenizer_instance": tokenizer,
        }
    elif model_name.startswith("claude-3"):
        client = Anthropic()
        return {
            "model_name": model_name,
            "model_instance": client,
        }
    else:
        raise ValueError(f"Unsupported model name: {model_name}")