import json
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os


# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
JSONL_PATH = "data/fitness.jsonl"
COLLECTION_NAME = "documents"
CHROMA_DB_PATH = "./chroma_db"
HASH_FILE = "data/.fitness_hash"


def data_has_changed(jsonl_path, hash_path):
    # Use file's last modified time and size
    stat = os.stat(jsonl_path)
    meta_str = f"{stat.st_mtime_ns}-{stat.st_size}"
    
    if os.path.exists(hash_path):
        with open(hash_path, "r") as f:
            old_meta = f.read().strip()
        if old_meta == meta_str:
            return False

    with open(hash_path, "w") as f:
        f.write(meta_str)
    return True



def load_model():
    return SentenceTransformer(MODEL_NAME)

def load_documents(path, limit=20):
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in tqdm(f, total=limit):
            item = json.loads(line)
            combined = f"{item['title_en']}. {item['content_en']}"
            docs.append(combined)
    return docs


def generate_embeddings(model, documents):
    print("Generating embeddings...")
    return model.encode(documents, show_progress_bar=True)


def init_chroma_collection(path, name):
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def add_documents_to_collection(collection, docs, embeddings):
    print("Adding to ChromaDB...")
    collection.add(
        documents=docs,
        embeddings=embeddings,
        ids=[f"doc_{i}" for i in range(len(docs))]
    )


def interactive_query_loop(model, collection):
    query = "Tell me about energy"
    while query and query.lower() != "exit":
        query_embedding = model.encode([query])[0]
        print("\nPerforming search...")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2
        )
        for id, doc, dist in zip(results["ids"][0], results[ "documents"][0], results["distances"][0]):
            print(f"Doc: {id} > {doc} (score: {dist:.4f})\n")
        print( "-" * 40)
        query = input("\nEnter your query (or 'exit'): ")


def main():
    model = load_model()
    collection = init_chroma_collection(CHROMA_DB_PATH, COLLECTION_NAME)

    if data_has_changed(JSONL_PATH, HASH_FILE):
        print("Data has changed")
        docs = load_documents(JSONL_PATH)
        embeddings = generate_embeddings(model, docs)
        add_documents_to_collection(collection, docs, embeddings)
    else:
        print("No changes in data.")

    interactive_query_loop(model, collection)


if __name__ == "__main__":
    main()
