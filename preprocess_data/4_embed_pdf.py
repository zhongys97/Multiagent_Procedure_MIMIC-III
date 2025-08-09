import os
import fitz  # PyMuPDF
import openai
import faiss
import numpy as np
import json
from openai import OpenAI
from tqdm import tqdm
import pickle

with open("./../api_keys.json", "r") as f:
    os.environ["OPENAI_API_KEY"] = json.load(f)["openai_api_key"]

# ---- CONFIGURATION ----
CHAPTERS_DIR = "/home/hice1/yzhong307/scratch/multi-agent_mimic3/MIMIC3_References_PDF"
METADATA_DIR = "/home/hice1/yzhong307/scratch/multi-agent_mimic3/MIMIC3_References_Metadata"
OUTPUT_PKL_DIR = "/home/hice1/yzhong307/scratch/multi-agent_mimic3/MIMIC3_RAG"
CHUNK_SIZE = 300
EMBED_MODEL = "text-embedding-3-small"

client = OpenAI()

def extract_chunks_from_pdf(pdf_path, chunk_size=300):
    doc = fitz.open(pdf_path)
    text = "".join([page.get_text() for page in doc])
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding

def preprare_one_chapter(metadata_path, one_chapter_pdf_dir, save_pkl_path):
    
    PMCID_to_title = {}
    for line in open(metadata_path, "r"):
        data = json.loads(line)
        if "pmcid" in data and "title" in data:
            PMCID_to_title[data["pmcid"]] = data["title"]

    # ---- LOAD & EMBED ----
    all_chunks = []
    chunk_sources = []
    for file in os.listdir(one_chapter_pdf_dir):
        if file.endswith(".pdf"):
            chunks = extract_chunks_from_pdf(os.path.join(one_chapter_pdf_dir, file), CHUNK_SIZE)
            all_chunks.extend(chunks)
            chunk_sources.extend([PMCID_to_title[file[:-4]]] * len(chunks)) # remove .pdf extension

    embeddings = [get_embedding(chunk) for chunk in tqdm(all_chunks)]

    # ---- FAISS INDEX ----
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))


    bundle = {
        "index": faiss.serialize_index(index),  # convert FAISS index to bytes
        "chunks": all_chunks,
        "sources": chunk_sources,
    }

    with open(save_pkl_path, "wb") as f:
        pickle.dump(bundle, f)


if __name__ == "__main__":

    chapters = [f for f in os.listdir(CHAPTERS_DIR) if os.path.isdir(os.path.join(CHAPTERS_DIR, f))]

    for chapter in chapters:
        metadata_path = os.path.join(METADATA_DIR, f"{chapter}_downloaded_references.jsonl")


        one_chapter_pdf_dir = os.path.join(CHAPTERS_DIR, chapter)
        save_pkl_path = os.path.join(OUTPUT_PKL_DIR, f"{chapter}.pkl")

        if os.path.exists(save_pkl_path):
            print(f"Skipping {chapter}, already processed.")
            continue
        
        preprare_one_chapter(metadata_path, one_chapter_pdf_dir, save_pkl_path)
