import os
import pickle
import time
from retriever.embedder import get_model, load_documents, encode_documents, encode_query
from retriever.vector_store import create_qdrant_collection, add_documents_to_index, query_index
from generator.prompt_template import build_prompt
from generator.llm_interface import call_llm


def initialize_or_build_index(jsonl_path, encoder_model, embedding_dim=384):
    """
    Loads or builds Qdrant index.
    """
    # Load docs from JSONL
    documents = load_documents(jsonl_path)
    print(f"Loaded {len(documents)} chunks.")

    # Create embeddings
    doc_embeddings = encode_documents(documents, encoder_model)

    # Create Qdrant collection
    create_qdrant_collection(doc_embeddings.shape[1])

    # Insert docs
    add_documents_to_index(documents, doc_embeddings)
    print("Qdrant index ready.")

    return documents

def main():
    load_start = time.time()
    jsonl_path = r"data/fitness.jsonl"
    encoder_model_name = 'all-MiniLM-L6-v2'
    encoder_model = get_model(encoder_model_name)
    chat_history = [] 

    documents = initialize_or_build_index(jsonl_path, encoder_model)

    print(f"Index and documents loaded in {time.time() - load_start:.2f} seconds.")
    while True:
        query = input("\nEnter your query (or 'exit' to quit): ").strip()
        start = time.time()

        if query.lower() == 'exit':
            break
        
        query_embedding = encode_query(query, encoder_model)
        results = query_index(query_embedding, top_k=3)

        if not results:
            print("No results found.")
            continue

        chunk_time = time.time()
        print("\nChunks retrieved in {:.2f} seconds:".format(chunk_time - start))

        gen_start = time.time()
        context = [res['document'] for res in results]
        prompt = build_prompt(context, query)
        answer, chat_history = call_llm(
            prompt,
            model_name="mistral:latest",
            history=chat_history,
            history_enabled=True,
        )

        print("\nAnswer:")
        print(answer)
        print("=" * 50)
        end = time.time()
        print(f"LLM response time: {end - gen_start:.2f} seconds.")

if __name__ == "__main__":
    main()
    