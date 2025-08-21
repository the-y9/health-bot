import os
import json
import numpy as np
from collections import defaultdict
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize, sent_tokenize
from rouge_score import rouge_scorer
from retriever.sql_emb import load_documents
import nltk
import sqlite3
from tqdm import tqdm


# nltk.download("punkt")

# === CONFIG ===
jsonl_path = r"data\fitness.jsonl"
expected_overlap = 5
min_chunk_words = 300
max_chunk_words = 500



# def load_documents(jsonl_path, short_limit=600, min_chunk_words=300, max_chunk_words=625, expected_overlap=50):
#     """
#     Load and chunk documents from JSONL file(s), sentence-aware chunking with word count boundaries and overlap.
    
#     - If article ≤ short_limit words → 1 chunk.
#     - If longer → chunk by sentences, each chunk between min_chunk_words and max_chunk_words.
#     - Overlap implemented by including sentences covering at least expected_overlap words from previous chunk.
#     """
    
#     def chunk_by_sentences(sentences, min_words, max_words, overlap_words):
#         chunks = []
#         current_chunk = []
#         current_length = 0
#         i = 0

#         while i < len(sentences):
#             sent = sentences[i]
#             sent_len = len(word_tokenize(sent))
            
#             # If adding this sentence would exceed max, close current chunk if big enough
#             if current_length + sent_len > max_words:
#                 if current_length >= min_words:
#                     chunks.append(" ".join(current_chunk))
#                     # Prepare overlap: count backward sentences until overlap_words reached
#                     overlap_chunk = []
#                     overlap_count = 0
#                     j = i - 1
#                     while j >= 0 and overlap_count < overlap_words:
#                         overlap_chunk.insert(0, sentences[j])
#                         overlap_count += len(word_tokenize(sentences[j]))
#                         j -= 1
#                     # Start new chunk with overlap sentences
#                     current_chunk = overlap_chunk.copy()
#                     current_length = sum(len(word_tokenize(s)) for s in current_chunk)
#                 else:
#                     # Not enough words, but chunk is full - force chunk
#                     chunks.append(" ".join(current_chunk))
#                     current_chunk = []
#                     current_length = 0

#             current_chunk.append(sent)
#             current_length += sent_len
#             i += 1
        
#         # Add last chunk
#         if current_chunk:
#             chunks.append(" ".join(current_chunk))

#         return chunks

#     def process_file(file_path):
#         file_documents = []
#         with open(file_path, 'r', encoding='utf-8') as f:
#             for doc_idx, line in enumerate(f):
#                 record = json.loads(line)
#                 title = record.get('title_en', '').strip()
#                 paragraphs = record.get('content_en', [])
#                 content = "\n".join(paragraphs).strip()
#                 full_text = f"{title}\n{content}" if title else content
                
#                 total_words = len(word_tokenize(full_text))

#                 if total_words <= short_limit:
#                     file_documents.append({
#                         'title': title,
#                         'chunk_id': f"{doc_idx}",
#                         'text': full_text
#                     })
#                 else:
#                     sentences = sent_tokenize(full_text)
#                     chunks = chunk_by_sentences(sentences, min_chunk_words, max_chunk_words, expected_overlap)
#                     for chunk_idx, chunk in enumerate(chunks):
#                         file_documents.append({
#                             'title': title,
#                             'chunk_id': f"{doc_idx}.{chunk_idx:02d}",
#                             'text': chunk
#                         })
#         return file_documents

#     all_documents = []
#     if os.path.isfile(jsonl_path) and jsonl_path.endswith('.jsonl'):
#         all_documents.extend(process_file(jsonl_path))
#     elif os.path.isdir(jsonl_path):
#         for root, _, files in os.walk(jsonl_path):
#             for file in files:
#                 if file.endswith('.jsonl'):
#                     full_path = os.path.join(root, file)
#                     all_documents.extend(process_file(full_path))
#     else:
#         raise ValueError(f"Invalid path: {jsonl_path}. Must be a .jsonl file or directory.")

#     return all_documents

# === Load full original documents ===
def load_full_articles(jsonl_path):
    articles = {}
    if os.path.isfile(jsonl_path):
        files = [jsonl_path]
    else:
        files = [os.path.join(root, file)
                 for root, _, files in os.walk(jsonl_path)
                 for file in files if file.endswith(".jsonl")]

    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                title = record.get('title_en', '')
                content = "\n".join(record.get('content_en', []))
                full_text = f"{title}\n{content}".strip()
                if full_text:
                    articles[title] = full_text
    return articles


def load_sql_articles(db_path):
    articles = {}
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM articles")
    
    for title, content in cursor.fetchall():
        content_text = str(content)
        full_text = f"{title}\n{content_text}".strip()
        if full_text:
            articles[title] = full_text
    
    conn.close()
    return articles


def audit_chunks(chunks, originals, min_chunk_words=30, max_chunk_words=300, expected_overlap=10):
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    smoothie = SmoothingFunction().method4
    chunk_issues = []

    # To track similarity scores for stats
    all_rouge1 = []
    all_rougeL = []
    all_bleu = []

    by_title = defaultdict(list)
    for c in chunks:
        by_title[c['title']].append(c)

    for title, chunk_list in tqdm(by_title.items(), total=len(by_title)):
        if title not in originals:
            continue

        original_text = originals[title]
        original_words = word_tokenize(original_text.lower())

        for i, chunk in enumerate(chunk_list):
            chunk_text = chunk['text'].strip()
            chunk_words = word_tokenize(chunk_text.lower())

            # 1. Length sanity check
            length = len(chunk_words)
            if length < min_chunk_words or length > max_chunk_words:
                chunk_issues.append({
                    'title': title,
                    'chunk_id': chunk['chunk_id'],
                    'issue': f"Chunk length out of bounds ({length} words)"
                })

            # 2. Boundary check (start/end on sentence)
            sentences = sent_tokenize(chunk_text)
            if len(sentences) > 1:
                if not chunk_text.startswith(sentences[0]) or not chunk_text.endswith(sentences[-1]):
                    chunk_issues.append({
                        'title': title,
                        'chunk_id': chunk['chunk_id'],
                        'issue': f"Chunk does not align with sentence boundaries"
                    })

            # 3. Semantic similarity (chunk vs. full doc)
            scores = rouge.score(original_text, chunk_text)
            rouge1 = scores['rouge1'].fmeasure
            rougeL = scores['rougeL'].fmeasure
            bleu = sentence_bleu([original_words], chunk_words, smoothing_function=smoothie)

            # Store similarity scores for summary
            all_rouge1.append(rouge1)
            all_rougeL.append(rougeL)
            all_bleu.append(bleu)

            if rouge1 < 0.5 or bleu < 0.4:
                chunk_issues.append({
                    'title': title,
                    'chunk_id': chunk['chunk_id'],
                    'issue': f"Low semantic similarity",
                    'rouge1': round(rouge1, 3),
                    'rougeL': round(rougeL, 3),
                    'bleu': round(bleu, 3)
                })

            # 4. Overlap check (with previous chunk)
            if i > 0:
                prev_words = word_tokenize(chunk_list[i - 1]['text'].lower())
                overlap = len(set(chunk_words[:expected_overlap]) & set(prev_words[-expected_overlap:]))
                if overlap < int(expected_overlap * 0.6):  # Allow 60% match
                    chunk_issues.append({
                        'title': title,
                        'chunk_id': chunk['chunk_id'],
                        'issue': f"Low word overlap with previous chunk ({overlap} words)"
                    })

    # Summary stats
    similarity_summary = {
        'avg_rouge1': round(np.mean(all_rouge1), 3),
        'min_rouge1': round(np.min(all_rouge1), 3),
        'max_rouge1': round(np.max(all_rouge1), 3),
        'avg_rougeL': round(np.mean(all_rougeL), 3),
        'avg_bleu': round(np.mean(all_bleu), 3)
    }

    return chunk_issues, similarity_summary

# === MAIN ===
if __name__ == "__main__":
    print("Audit started...")
    db = "database.db"
    originals = load_sql_articles(db)
    print(len(originals), "docs")

    chunks = load_documents(db)
    print(len(chunks), "chunks")

    issues, summary = audit_chunks(chunks, originals)

    if not issues:
        print("All chunks passed the quality audit.")
    else:
        unique_chunk_ids = set((issue['title'], issue['chunk_id']) for issue in issues)
        print(f"Found {len(issues)} total issues in {len(unique_chunk_ids)} unique chunks across {len(originals)} docs.")

        # with open("audit2.md", 'w', encoding='utf-8') as f:
        #     for issue in tqdm(issues, total=len(issues)):
        #         line = f"- {issue['title']} [Chunk {issue['chunk_id']}] — {issue['issue']}"
        #         if 'rouge1' in issue:
        #             line += f" | R1: {issue['rouge1']} | RL: {issue['rougeL']} | BLEU: {issue['bleu']}"
        #         f.write(line + '\n')

    # print("\nSimilarity Score Summary (All Documents)")
    # for key, val in summary.items():
    #     print(f"- {key}: {val}")
    with open("audit.md",'w') as f:
        f.write("## Similarity Score Summary (Chunk Preservation)")
        for key, val in summary.items():
            f.write(f"\n- {key}: {val}")

