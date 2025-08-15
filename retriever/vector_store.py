# retriever/vector_store.py
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)  
# client = QdrantClient(url="YOUR_QDRANT_URL", api_key="YOUR_API_KEY")

COLLECTION_NAME = "documents"

def create_qdrant_collection(dim):
    """
    Creates or recreates a Qdrant collection for storing embeddings.
    """
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
    )

def add_documents_to_index(documents, embeddings):
    """
    Adds documents & their embeddings to Qdrant.
    """
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=emb.tolist(), payload={"document": doc})
        for doc, emb in zip(documents, embeddings)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)

def query_index(query_embedding, top_k=5):
    """
    Queries Qdrant and returns top_k most similar documents.
    """
    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=top_k
    )
    return [
        {"score": r.score, "document": r.payload["document"]}
        for r in search_result
    ]

def save_index(index_path, metadata_path):
    """
    Not needed for Qdrant (persistent storage).
    """
    pass

def load_index(index_path, metadata_path):
    """
    Not needed for Qdrant (persistent storage).
    """
    pass
