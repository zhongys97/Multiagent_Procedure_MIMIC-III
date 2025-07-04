import faiss
import os
import json
import numpy as np
from openai import OpenAI
import pickle
from prompts.private_thought import rag_prompt
from utils.helper import format_rag_response
from utils.call_llms import get_response

INDICES_DIR = "./MIMIC3_RAG/"

with open("./api_keys.json", "r") as f:
    os.environ["OPENAI_API_KEY"] = json.load(f)["openai_api_key"]

client = OpenAI()

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

def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

def query_faiss(index, chunks, sources, question: str, top_k: int = 5):
    query_vec = np.array([get_embedding(question)], dtype="float32")
    D, I = index.search(query_vec, top_k)

    res = []
    for i in range(len(I[0])):
        res.append({
            "chunk": chunks[I[0][i]],
            "source": sources[I[0][i]],
        })
    return res



def generate_rag_responses(chapter_idx: str, questions: list, indices_dir: str, model_info: dict) -> str:

    index_pkl_name = chapter_idx_to_pkl_name[chapter_idx]

    expert_domain_str = " ".join(index_pkl_name.split("_")[1:]).replace(".pkl", "")
    index_pkl_path = os.path.join(indices_dir, index_pkl_name)

    with open(index_pkl_path, "rb") as f:
        faiss_index_and_texts = pickle.load(f)

    # Load FAISS index
    index = faiss.deserialize_index(faiss_index_and_texts["index"])

    # Load associated text chunks and source filenames
    chunks = faiss_index_and_texts["chunks"]
    sources = faiss_index_and_texts["sources"]

    combined_response = []
    for question in questions:
        top_chunks = query_faiss(index, chunks, sources, question, top_k=5)
        
        context_text = ""
        for chunk in top_chunks:
            context_text += f"{chunk['chunk']} (Source: {chunk['source']})\n\n"

        prompt = rag_prompt.format(
            expert_domain_str,
            context_text,
            questions
        )

        response_str = get_response(prompt, model_info)

        # response_str = response.choices[0].message.content.strip()
        response_dict = format_rag_response(response_str)
        combined_response.append({"Question": question, "Response": response_dict})
        
    return combined_response


if __name__ == "__main__":
    chapter_idx = "extra"
    questions = ["what is the clinical symptoms of severe pneumonia", "What is the typical treatment for pneumonia?"]
    response = generate_rag_responses(chapter_idx, questions, indices_dir=INDICES_DIR)
    print(response)
    
