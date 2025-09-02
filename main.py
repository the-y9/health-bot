from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import time
from contextlib import asynccontextmanager

# Comment out AI/Docker heavy imports to speed up startup
# from retriever.sql_emb import load_documents, Embedder
# from retriever.vector_store import collection_exists, create_qdrant_collection, add_documents_to_index, query_index
# from generator.prompt_template import build_prompt
# from generator.llm_interface import LLMInterface
# from docker import docker_image_exists, pull_docker_image, run_docker_container

# Import your article routes
from routes.article_routes import router as article_router
from init_db import init_db
import os

# ==== Config ====
# FILE_PATH = "data/fitness.jsonl"
FILE_PATH = "database.db"
ENCODER_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3
image = "qdrant/qdrant"
container_name = "health-bot-qdrant"
storage_path = "qdrant_storage"

# ==== Models ====
class QueryRequest(BaseModel):
    query: str
    user_id: str 

class QueryResponse(BaseModel):
    answer: str
    results: List[dict]
    timing: dict

# ==== Globals (set during startup) ====
# llm = None
# embedder = None
# documents = None
# llm_sessions = {} 

# ==== Startup/Shutdown Events ====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - only initialize database
    print("Initializing database...")
    if not os.path.exists(FILE_PATH):
        init_db()
    print("Database ready!")
    
    # Comment out heavy AI/Docker initialization
    # global llm, embedder, documents, llm_sessions
    # 
    # if not docker_image_exists(image):
    #     pull_docker_image(image)
    # run_docker_container(image, container_name, storage_path)
    # 
    # print("Loading documents...")
    # documents = load_documents(FILE_PATH)
    # print(f"Loaded {len(documents)} documents")
    # 
    # print("Initializing Embedder and LLM...")
    # embedder = Embedder(model_name=ENCODER_MODEL)
    # 
    # if not collection_exists():
    #     print("Creating and indexing Qdrant collection...")
    #     doc_embeddings = embedder.encode_documents(documents)
    #     create_qdrant_collection(doc_embeddings.shape[1])
    #     add_documents_to_index(documents, doc_embeddings)
    #     print("Indexing complete.")
    # else:
    #     print("Qdrant collection already exists, skipping indexing.")
    
    yield
    # Shutdown (if needed)

# ==== FastAPI App ====
app = FastAPI(
    title="Health Bot API",
    description="API for health articles with AI chat capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Include article routes
app.include_router(article_router)

@app.get("/")   
def read_root():
    return {"message": "Health Bot API is running. Use /articles endpoints or /query to post questions."}

# ==== Query Endpoint (Temporarily Disabled) ====
@app.post("/query", response_model=QueryResponse)
def ask_question(req: QueryRequest):
    # Temporarily return a placeholder response to avoid errors
    return QueryResponse(
        answer="AI query functionality is temporarily disabled for faster startup. Please use /articles endpoints instead.",
        results=[],
        timing={"embedding_time": 0, "generation_time": 0}
    )
    
    # Original AI code commented out:
    # start = time.time()
    # 
    # # Get or create LLMInterface for this user
    # if req.user_id not in llm_sessions:
    #     llm_sessions[req.user_id] = LLMInterface(history_enabled=True)
    # user_llm = llm_sessions[req.user_id]
    # 
    # # Encode query and retrieve context
    # query_embedding = embedder.encode_query(req.query)
    # results = query_index(query_embedding, top_k=TOP_K)
    # chunk_time = time.time()
    # 
    # if not results:
    #     return QueryResponse(
    #         answer="No relevant documents found.",
    #         results=[],
    #         timing={"embedding_time": chunk_time - start, "generation_time": 0}
    #     )
    # 
    # context = [res["document"] for res in results]
    # prompt = build_prompt(context, req.query)
    # answer = user_llm.call_llm(prompt)
    # end = time.time()
    # 
    # return QueryResponse(
    #     answer=answer,
    #     results=results,
    #     timing={
    #         "embedding_time": chunk_time - start,
    #         "generation_time": end - chunk_time
    #     }
    # )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)