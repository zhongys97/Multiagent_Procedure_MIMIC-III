import json
import os
from openai import OpenAI
from prompts.private_thought import raise_questions_for_rag, digest_rag_response
from pipeline.query_literature import generate_rag_responses
from utils.setup import setup_agents
from utils.call_llms import get_response
from utils.get_patient_context import get_patient_context_per_admission
from utils.truncate_prompts import retain_most_recent_info
from ast import literal_eval

with open('api_keys.json', 'r') as f:
    api_keys = json.load(f)

os.environ["OPENAI_API_KEY"] = api_keys["openai_api_key"]

client = OpenAI()

agents = setup_agents(internal_memory=True)  # Assuming internal memory is needed for this task

def generate_questions(patient_data, previous_discussions, expert_domain, model_info):
    """
    Generate a prompt to raise questions for RAG based on patient data and previous discussions.
    """
    prompt = raise_questions_for_rag.format(
        patient_data,
        previous_discussions,
        expert_domain
    )
    
    list_of_questions = get_response(prompt, model_info)
    
    try:
        questions = literal_eval(list_of_questions)
        if isinstance(questions, list) and len(questions) == 2:
            return questions
        else:
            raise ValueError("Response is not a valid list of two questions.")
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing response: {e}")
        return ["", ""]  # Return empty questions if parsing fails


def reflect_on_rag_response(expert_domain, expert_private_memory, rag_combined_response, model_info):

    prompt = digest_rag_response.format(
        expert_domain,
        expert_private_memory,
        rag_combined_response
    )

    response = get_response(prompt, model_info)
    
    return response


def update_agent_private_thinking(round_idx, chapter_idx, patient_data, previous_discussions, expert_private_memory, model_info, rag_data_dir, alone=False):

    if not alone:
        expert_domain = agents[chapter_idx]["expert_domain_str"]
        expert_name = agents[chapter_idx]["expert_name"]
    else:
        expert_domain = "primary care"
        expert_name = "expert in primary care"

    new_agent_memory_item = {"round_idx": round_idx,
                             "chapter_idx": chapter_idx,
                             "expert": expert_name,}
    
    list_of_questions = generate_questions(patient_data, previous_discussions, expert_domain, model_info)
    new_agent_memory_item["questions_for_rag"] = list_of_questions

    rag_combined_response = generate_rag_responses(chapter_idx, list_of_questions, indices_dir=rag_data_dir, model_info=model_info, alone=alone)
    new_agent_memory_item["rag_response"] = rag_combined_response

    new_insight = reflect_on_rag_response(expert_domain, expert_private_memory, rag_combined_response, model_info)
    new_agent_memory_item["new_insight"] = new_insight

    expert_private_memory.append(new_agent_memory_item)
    return expert_private_memory



if __name__ == "__main__":

    discussion_json_path = "/home/hice1/yzhong307/scratch/multi-agent_mimic3/mimic_iii_subject_3097_admission_0_discussion.json"

    with open(discussion_json_path, "r") as f:
        discussions = json.load(f)["discussion"]

    chapter_idx = "1"  # Example chapter index
    expert_domain = agents[chapter_idx]["expert_domain_str"]

    patient_ehr_json_path = "mimic_iii_subject_3097.db.json"  # Example patient EHR JSON path
    with open(patient_ehr_json_path, "r") as f:
        patient_ehr = json.load(f)

    for i, admission in enumerate(patient_ehr["admissions"]):
        admission_info = get_patient_context_per_admission(patient_ehr, i)

        if admission_info["skip"]:
            continue
        else:
            patient_context = admission_info["context"]

        previous_discussions = []

        list_of_questions = generate_questions(
            patient_context,
            previous_discussions,
            expert_domain
        )

        rag_response = generate_rag_responses(chapter_idx, list_of_questions, indices_dir="./MIMIC3_RAG/")
        # print(rag_response)

        new_insight = reflect_on_rag_response(expert_domain, "", rag_response)
        print(new_insight)
