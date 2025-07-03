import json
import os
from openai import OpenAI
from prompts.private_thought import raise_questions_for_rag, rag_prompt, reflect_on_rag_response
from pipelines.query_literature import generate_rag_responses


with open('api_keys.json', 'r') as f:
    api_keys = json.load(f)

os.environ["OPENAI_API_KEY"] = api_keys["openai_api_key"]

client = OpenAI()


def generate_questions(patient_data, previous_discussions, expert_domain):
    """
    Generate a prompt to raise questions for RAG based on patient data and previous discussions.
    """
    prompt = raise_questions_for_rag.format(
        patient_data,
        previous_discussions,
        expert_domain
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=0.5
    )
    
    return response.choices[0].message.content.strip()


def reflect_on_rag_response(expert_domain, expert_private_memory, rag_combined_response):

    prompt = reflect_on_rag_response.format(
        expert_domain,
        expert_private_memory,
        rag_combined_response
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=0.5
    )
    
    return response.choices[0].message.content.strip()


def update_agent_private_thinking(expert_domain, patient_data, previous_discussions):
    
    questions = generate_questions(patient_data, previous_discussions, expert_domain)

    rag_combined_response = generate_rag_responses


if __name__ == "__main__":

    