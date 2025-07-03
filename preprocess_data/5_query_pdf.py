import faiss
import os
import json
import numpy as np
from openai import OpenAI
import pickle

with open("./../api_keys.json", "r") as f:
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
    response = client.embeddings.create(input=[text], model=model)
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



def generate_rag_responses(chapter_idx: str, question: str, indices_dir: str = "./../MIMIC3_RAG/") -> str:

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


    top_chunks = query_faiss(index, chunks, sources, question, top_k=5)
    
    context_text = ""
    for chunk in top_chunks:
        context_text += f"{chunk['chunk']} (Source: {chunk['source']})\n\n"

    
    prompt = f"""
        You are an expert in {expert_domain_str}.
        Use the following literature to answer the user's question.
        --- Relevant Literature ---
        {context_text}
        --- Question ---
        {question}
        --- Answer ---
        Please provide an accurate response based on the provided literature.
        Besides your answer, please also provide a rating of the relevance of the literature to the question.
        For example, if the question is about typical blood pressure for pulmonary hypertension, but the literature is about mental disorders, you should report a low relevance.
        However, if the question is about the psychological aspect of pulmonary hypertension, you should report a slightly higher relevance.
        Finally, if the question is directly addressed by the literature, you should report a high relevance.
        The relevance score is an integer between 0 and 10, where 0 means not relevant at all, and 10 means highly relevant.
        Return the answer in 'Answer: <your answer here>', 'Relevance: <score>' format.
    """

    print(prompt)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    response_str = response.choices[0].message.content.strip()
    return response_str
    

if __name__ == "__main__":
    chapter_idx = "7"  # Example chapter index
    # question = "What are the mental signs of jaundice?"
    question = "what are treatment are recommended for depression?"
    
    response = generate_rag_responses(chapter_idx, question)
    print(response)
    
