import os
import pickle
import time
from retriever.embedder import load_documents, Embedder
from retriever.vector_store import collection_exists, create_qdrant_collection, add_documents_to_index, query_index
from generator.prompt_template import build_prompt
from generator.llm_interface import LLMInterface

def main():
    start_time = time.time()

    jsonl_path = r"data/fitness.jsonl"
    encoder_model_name = 'all-MiniLM-L6-v2'

    # Load documents
    load_start = time.time()
    documents = load_documents(jsonl_path)
    load_end = time.time()
    print(f"Documents loaded in {load_end - load_start:.2f} seconds\nDocuments found: {len(documents)}")

    # Initialize LLM and Embedder
    init_start = time.time()
    llm = LLMInterface(history=True)
    llm_end = time.time()
    print(f"LLM initialized in {llm_end - init_start:.2f} seconds")
    embedder = Embedder(model_name=encoder_model_name)
    emb_end = time.time()
    print(f"Embedder initialized in {emb_end - llm_end:.2f} seconds")

    # Check for collection and possibly create & index
    index_start = time.time()
    if not collection_exists():
        print("Creating Qdrant collection and indexing documents...")
        doc_embeddings = embedder.encode_documents(documents)
        create_qdrant_collection(doc_embeddings.shape[1])
        add_documents_to_index(documents, doc_embeddings)
    else:
        print("Qdrant collection already exists, skipping indexing.")
    index_end = time.time()
    print(f"Indexing step completed in {index_end - index_start:.2f} seconds")

    total_end = time.time()
    print(f"Total setup time: {total_end - start_time:.2f} seconds")

    while True:
        query = input("\nEnter your query (or 'exit' to quit): ").strip()
        start = time.time()

        if query.lower() == 'exit':
            break
        
        query_embedding = embedder.encode_query(query)
        results = query_index(query_embedding, top_k=3)

        if not results:
            print("No results found.")
            continue

        chunk_time = time.time()

        context = [res['document'] for res in results]
        prompt = build_prompt(context, query)

        print("\nAnswer:")
        print(llm.call_llm(prompt))
        print("=" * 50)
        end = time.time()
        print(f"Response time: {chunk_time - start:.2f}s + {end - chunk_time:.2f}s.")

if __name__ == "__main__":
    main()
    