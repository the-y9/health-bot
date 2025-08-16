import os
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

def chunk_text(text, size, overlap):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i:i + size])
        if chunk:
            chunks.append(chunk)
    return chunks

def load_documents(db_path='database.db', long_chunk_size=300, short_chunk_size=550, overlap=50):
    """
    Load and chunk articles from a SQLite database.
    Short articles are kept whole, long ones are split into overlapping chunks.
    Returns a list of dicts with 'title', 'chunk_id', and 'text'.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content, word_count FROM articles")
    rows = cursor.fetchall()
    conn.close()

    all_documents = []

    for row_id, title, content, word_count in rows:
        if not content:
            continue

        full_text = f"{title}\n{content}"

        if word_count < short_chunk_size:
            all_documents.append({
                'title': title,
                'chunk_id': row_id,
                'text': full_text
            })
        else:
            chunks = chunk_text(full_text, long_chunk_size, overlap)
            for idx, chunk in enumerate(chunks):
                all_documents.append({
                    'title': title,
                    'chunk_id': f"{row_id}.{idx:02d}",
                    'text': chunk
                })

    return all_documents

class Embedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def encode_documents(self, docs, batch_size=32):
        texts = [doc['text'] for doc in docs]
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)
        return np.array(embeddings)

    def encode_query(self, query):
        return self.model.encode([query], normalize_embeddings=True)[0]
