from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import time

from retriever.sql_emb import load_documents, Embedder
from retriever.vector_store import collection_exists, create_qdrant_collection, add_documents_to_index, query_index
from generator.prompt_template import build_prompt
from generator.llm_interface import LLMInterface
from docker import docker_image_exists, pull_docker_image, run_docker_container

# ==== Config ====
# FILE_PATH = "data/fitness.jsonl"
FILE_PATH = "database.db"
ENCODER_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3
image = "qdrant/qdrant"
container_name = "health-bot-qdrant"
storage_path = "qdrant_storage"

# ==== FastAPI App ====
app = FastAPI()

# ==== Models ====
class QueryRequest(BaseModel):
    query: str
    user_id: str 

class QueryResponse(BaseModel):
    answer: str
    results: List[dict]
    timing: dict

# ==== Globals (set during startup) ====
llm = None
embedder = None
documents = None
llm_sessions = {} 

# ==== Startup Event ====
@app.on_event("startup")
def setup():
    global llm, embedder, documents, llm_sessions

    if not docker_image_exists(image):
        pull_docker_image(image)
    run_docker_container(image, container_name, storage_path)

    print("Loading documents...")
    documents = load_documents(FILE_PATH)
    print(f"Loaded {len(documents)} documents")

    print("Initializing Embedder and LLM...")
    embedder = Embedder(model_name=ENCODER_MODEL)

    if not collection_exists():
        print("Creating and indexing Qdrant collection...")
        doc_embeddings = embedder.encode_documents(documents)
        create_qdrant_collection(doc_embeddings.shape[1])
        add_documents_to_index(documents, doc_embeddings)
        print("Indexing complete.")
    else:
        print("Qdrant collection already exists, skipping indexing.")

@app.get("/")
def read_root():
    return {"message": "Health Bot API is running. Use /query to post questions."}

# ==== Query Endpoint ====
@app.post("/query", response_model=QueryResponse)
def ask_question(req: QueryRequest):
    start = time.time()

    # Get or create LLMInterface for this user
    if req.user_id not in llm_sessions:
        llm_sessions[req.user_id] = LLMInterface(history_enabled=True)
    user_llm = llm_sessions[req.user_id]

    # Encode query and retrieve context
    query_embedding = embedder.encode_query(req.query)
    results = query_index(query_embedding, top_k=TOP_K)
    chunk_time = time.time()

    if not results:
        return QueryResponse(
            answer="No relevant documents found.",
            results=[],
            timing={"embedding_time": chunk_time - start, "generation_time": 0}
        )

    context = [res["document"] for res in results]
    prompt = build_prompt(context, req.query)
    answer = user_llm.call_llm(prompt)
    end = time.time()

    return QueryResponse(
        answer=answer,
        results=results,
        timing={
            "embedding_time": chunk_time - start,
            "generation_time": end - chunk_time
        }
    )

