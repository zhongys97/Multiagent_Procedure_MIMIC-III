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
    elif model_name.startswith("claude-3"):
        client = Anthropic()
        return {
            "model_name": model_name,
            "model_instance": client,
        }
    elif model_name == "qwen2":
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        import torch

        token = os.environ["HUGGINGFACE_HUB_TOKEN"]

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        model_id = "Qwen/Qwen2-7B"

        
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            quantization_config=quantization_config,
            attn_implementation="flash_attention_2",
            trust_remote_code=True
        ).eval()


        # YARN & Long context config (optional, many Qwen models have this in config.json already)
        if hasattr(model.config, "use_sliding_window") and hasattr(model.config, "slide_window_size"):
            model.config.use_sliding_window = True
            model.config.slide_window_size = 8192  # or 4096 or model default

        if hasattr(model.config, "max_position_embeddings"):
            print(f"Max context: {model.config.max_position_embeddings} tokens")

        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        tokenizer.model_max_length = model.config.max_position_embeddings

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        return {
            "model_name": model_name,
            "model_instance": model,
            "tokenizer_instance": tokenizer,
        }
    elif "deepseek" in model_name:

        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        import torch

        model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

        tokenizer = AutoTokenizer.from_pretrained(model_id)

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,  # Use bfloat16 if on A100/H100
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"  # nf4 is recommended
        )

        # Load the model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
            attn_implementation="flash_attention_2",
            max_position_embeddings=131072,  # Explicitly set to 128K (if model supports it)
            rope_scaling={"type": "dynamic", "factor": 4.0}  # RoPE scaling for extrapolation
        )
        model.eval()
        return {
            "model_name": model_name,
            "model_instance": model,
            "tokenizer_instance": tokenizer,
        }

    elif model_name == "medgemma":
        import transformers

        # transformers.logging.ERROR
        transformers.logging.set_verbosity_error()

        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        from huggingface_hub import login
        import torch
        torch._dynamo.config.cache_size_limit = 1024

        model_id = "google/medgemma-4b-it"

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True, # Keep this if MedGemma needs it
            attn_implementation="flash_attention_2"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        return {
            "model_name": model_name,
            "model_instance": model,
            "tokenizer_instance": tokenizer,
        }
    elif model_name == "OpenBioLLM":

        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from huggingface_hub import login
        import torch

        model_id = "aaditya/Llama3-OpenBioLLM-70B"

        tokenizer = AutoTokenizer.from_pretrained(model_id)

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,  # Use bfloat16 if on A100/H100
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"  # nf4 is recommended
        )

        # Load the model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
            attn_implementation="flash_attention_2"
        ).eval()

        return {
            "model_name": model_name,
            "model_instance": model,
            "tokenizer_instance": tokenizer,
        }

    else:
        raise ValueError(f"Unsupported model name: {model_name}")