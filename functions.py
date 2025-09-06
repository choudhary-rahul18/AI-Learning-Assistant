import re
import os
import fitz # PyMuPDF
from typing import List
from io import BytesIO
import numpy as np
from langchain.schema import Document
import shutil
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
from rank_bm25 import BM25Okapi


def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")
model = get_model()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "user_session")

Langs = {"Hindi":'hi', "English":'en',"Bengali":'bn',"Chinese":'zh',
          "Tamil":'ta',"Telugu":'te'}

Models = {"Smalest_quen_model": "qwen:1.8b", "Medium_quen_model": "qwen:7b", "Quen_Model": "qwen:14b"}


def embed_index_chunks_hybrid(sample_chunks, session_id: str, session_dir=SESSION_DIR):
    """"Create and save hybrid retrieval indices"""
    if session_dir is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        session_dir = os.path.join(BASE_DIR, "user_session")
    
    session_path = os.path.join(session_dir, session_id)
    os.makedirs(session_path, exist_ok=True)

    # 1. Semantic indexing (FAISS)
    model = get_model()
    embeddings = model.encode(sample_chunks, convert_to_numpy=True)
    dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dim)
    faiss_index.add(embeddings)

    # 2. Keyword indexing (BM25)
    tokenized_chunks = [chunk.split() for chunk in sample_chunks]
    bm25_index = BM25Okapi(tokenized_chunks)

    # Save all components
    faiss.write_index(faiss_index, os.path.join(session_path, "faiss_index.idx"))
    with open(os.path.join(session_path, "chunks.pkl"), "wb") as f:
        pickle.dump(sample_chunks, f)
    with open(os.path.join(session_path, "bm25_index.pkl"), "wb") as f:
        pickle.dump(bm25_index, f)

    return faiss_index, bm25_index

def Video_Transcript(video_url, Language):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", video_url)
    if match:
        video_id = match.group(1)
    Lang_code = Langs[Language]
    ytt_api = YouTubeTranscriptApi()
    fetched_transcript= ytt_api.fetch(video_id,languages=[Lang_code, 'en'])
    text_output = []
    for snippet in fetched_transcript:
        text_output.append(snippet.text)
    single_string_space = " ".join(text_output)
    text_output = [single_string_space]
    return text_output   # It will give a list which contains all transcript as a single string.

#Function to recursively load all .pdf files
def load_pdfs_from_folder(root_folder):
    documents = []
    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.pdf'):
                filepath = os.path.join(foldername, filename)
                try:
                    doc = fitz.open(filepath)
                    content = ""
                    for page in doc:
                        content += page.get_text()
                    documents.append(Document(page_content=content, metadata={"source": filepath}))
                except Exception as e:
                    print(f"Failed to read {filepath}: {e}")
    return documents


def chunks_from_doc(response_data):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    
    # Handle different response formats
    if isinstance(response_data, dict):
        if "documents" in response_data:
            documents = response_data["documents"]
        else:
            # If no "documents" key, treat the entire response as a single document
            documents = [{"page_content": str(response_data)}]
    elif isinstance(response_data, list):
        documents = response_data
    else:
        documents = [{"page_content": str(response_data)}]
    
    # Convert to Document objects if needed
    processed_docs = []
    for doc in documents:
        if isinstance(doc, Document):
            processed_docs.append(doc)
        elif isinstance(doc, dict):
            processed_docs.append(
                Document(
                    page_content=doc.get("page_content", str(doc)),
                    metadata=doc.get("metadata", {})
                )
            )
        else:
            processed_docs.append(Document(page_content=str(doc)))
    
    # Split into chunks
    chunks = text_splitter.split_documents(processed_docs)
    return [chunk.page_content for chunk in chunks]


def retrieve_top_chunks_hybrid(query, top_k, session_id:str, session_dir=SESSION_DIR):

    session_path = os.path.join(session_dir, session_id)
    """Hybrid retrieval with RRF fusion and deduplication"""
    # Load indices and data
    faiss_index = faiss.read_index(os.path.join(session_path, "faiss_index.idx"))
    with open(os.path.join(session_path, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)
    with open(os.path.join(session_path, "bm25_index.pkl"), "rb") as f:
        bm25_index = pickle.load(f)

    # Semantic search (FAISS)
    model = get_model()
    query_embed = model.encode([query])
    _, faiss_ids = faiss_index.search(query_embed, top_k * 2)
    faiss_ids = faiss_ids[0].tolist()  # Convert to list

    # Keyword search (BM25)
    tokenized_query = query.split()
    bm25_scores = bm25_index.get_scores(tokenized_query)
    bm25_ids = np.argsort(bm25_scores)[-top_k * 2:][::-1].tolist()

    # RRF Fusion with deduplication
    registry = {}
    k = 60  # RRF constant

    # Register FAISS results
    for rank, chunk_id in enumerate(faiss_ids):
        registry.setdefault(chunk_id, {"faiss_rank": rank})

    # Register BM25 results
    for rank, chunk_id in enumerate(bm25_ids):
        if chunk_id in registry:
            registry[chunk_id]["bm25_rank"] = rank
        else:
            registry[chunk_id] = {"bm25_rank": rank}

        # Calculate RRF scores - MISSING CODE
    for chunk_id in registry:
        faiss_rrf = 1 / (registry[chunk_id].get("faiss_rank", 1000) + k)
        bm25_rrf = 1 / (registry[chunk_id].get("bm25_rank", 1000) + k)
        registry[chunk_id]["final_score"] = faiss_rrf + bm25_rrf

    # Get top-k unique chunks
    sorted_ids = sorted(registry.keys(),
                        key=lambda x: registry[x]["final_score"],
                        reverse=True)[:top_k]

    return [chunks[i] for i in sorted_ids]



def reset_session(session_dir=SESSION_DIR):
    pass

def delete_embeddings(session_id, session_dir=SESSION_DIR):
    session_path = os.path.join(session_dir, session_id)
    # Delete prior index files if they exist
    index_path = os.path.join(session_path, "faiss_index.idx")
    chunks_path = os.path.join(session_path, "chunks.pkl")

    for file_path in [index_path, chunks_path]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted existing file: {file_path}")

def delete_mcqs(session_dir="MCQs"):

    mcqs_json_path = os.path.join(session_dir, "mcqs.json")
    mcqs_txt_path = os.path.join(session_dir, "mcqs.txt")
    for file_path in [mcqs_json_path, mcqs_txt_path]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted existing file: {file_path}")


#------------------------------------------------------------------------------------------------------------------------------
def process_pdf_files_updated(uploaded_files: list) -> list:
    documents = []
    
    for file in uploaded_files:
        # Skip non-PDF files
        if not file.filename.lower().endswith('.pdf'):
            continue
        try:
            # Read file content into memory
            file_content = file.read()
            
            # Create in-memory PDF stream
            with BytesIO(file_content) as pdf_stream:
                # Open PDF from memory
                with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
                    content = ""
                    # Extract text from each page (same as original)
                    for page in doc:
                        content += page.get_text()
                    
                    # Create document with ORIGINAL metadata format
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={"source": file.filename}
                        )
                    )
        except Exception as e:
            print(f"Failed to process {file.filename}: {e}")

    return documents

def process_pdf_content(uploaded_files: list, session_id: str) -> str:
    documents = process_pdf_files_updated(uploaded_files)
    
    if not documents:
        raise ValueError("No valid PDF files were processed.")
    else:
        # chunks = chunks_from_doc(documents)
        # embed = embed_index_chunks_hybrid(chunks, session_id)
        return f"{len(documents)} PDF files processed successfully."

