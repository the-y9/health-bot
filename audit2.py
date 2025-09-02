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
        f.write("## Similarity Score Summary (Chunk Preservation - Dev)")
        for key, val in summary.items():
            f.write(f"\n- {key}: {val}")

