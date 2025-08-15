# generator/prompt_template.py

def build_prompt(context_chunks, query):
    context_text = "\n\n".join([chunk['text'] for chunk in context_chunks])
    prompt = f"""You are an intelligent assistant. Use the following context to answer the query.

Context:
{context_text}

Query: {query}

Answer:"""
    return prompt
