# retriever/embedder.py

from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os

def load_documents(jsonl_path, long_chunk_size=300, short_chunk_size=550, overlap=50):
    """
    Load and chunk documents from a JSONL file or a directory containing JSONL files (recursively).
    Articles with fewer than `short_chunk_size` words are kept whole.
    Longer articles are split into overlapping chunks of `long_chunk_size` words.
    """

    def chunk_text(text, size, overlap):
        words = text.split()
        chunks = []
        for i in range(0, len(words), size - overlap):
            chunk = " ".join(words[i:i + size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def process_file(file_path):
        file_documents = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                title = record.get('title_en', '')
                paragraphs = record.get('content_en', '')
                content = paragraphs if isinstance(paragraphs, str) else ' '.join(paragraphs)

                full_text = f"{title}\n{content}"
                words = content.split()

                if len(words) < short_chunk_size:
                    # Keep short articles as a single chunk
                    file_documents.append({
                        'title': title,
                        'chunk_id': 0,
                        'text': full_text
                    })
                else:
                    # Split long articles into overlapping chunks
                    chunks = chunk_text(full_text, long_chunk_size, overlap)
                    for idx, chunk in enumerate(chunks):
                        file_documents.append({
                            'title': title,
                            'chunk_id': idx,
                            'text': chunk
                        })
        return file_documents

    all_documents = []

    if os.path.isfile(jsonl_path) and jsonl_path.endswith('.jsonl'):
        all_documents.extend(process_file(jsonl_path))
    elif os.path.isdir(jsonl_path):
        for root, _, files in os.walk(jsonl_path):
            for file in files:
                if file.endswith('.jsonl'):
                    full_path = os.path.join(root, file)
                    all_documents.extend(process_file(full_path))
    else:
        raise ValueError(f"Invalid path: {jsonl_path}. Must be a .jsonl file or directory.")

    return all_documents


class Embedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def encode_documents(self, docs, batch_size=32):
        """
        Encodes a list of document strings into embeddings.
        """
        texts = [doc['text'] for doc in docs]
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)
        return np.array(embeddings)
    
    def encode_query(self, query):
        """
        Encodes a single query string.
        """
        return self.model.encode([query], normalize_embeddings=True)[0]
