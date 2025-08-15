# generator/llm_interface.py

import subprocess
import json

import json
import requests

def call_llm(prompt,
             model_name="mistral:latest",
             history=None,
             history_enabled=False,
             num_ctx=4096,
             temperature=0.2,
             top_k=40,
             top_p=0.9,
             repeat_penalty=1.2):
    """
    Sends a prompt (and optional history) to a local Ollama LLM API and returns the response.
    
    Parameters:
        - prompt (str): The user prompt.
        - model_name (str): The LLM model name.
        - history (list): List of past messages (dicts with 'role' and 'content').
        - history_enabled (bool): Whether to include and update history.
        - num_ctx, temperature, top_k, top_p, repeat_penalty: LLM config params.
        
    Returns:
        - response text from the LLM
        - updated history (if enabled), else None
    """
    if history is None:
        history = []

    messages = history.copy() if history_enabled else []
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "options": {
                    "num_ctx": num_ctx,
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p,
                    "repeat_penalty": repeat_penalty
                }
            },
            stream=True
        )
        response.raise_for_status()

        answer = ""
        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    answer += chunk["message"]["content"]
                else:
                    print(f"Unexpected chunk format: {chunk}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error on line: {line} — {e}")

        updated_history = None
        if history_enabled:
            updated_history = history + [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer}
            ]

        return answer, updated_history

    except Exception as e:
        return f"Error communicating with LLM: {e}", history if history_enabled else None



# class LLMInterface:
#     def __init__(self, model_name="mistral:latest", history=False):
#         self.model_name = model_name
#         self.history_enabled = history
#         self.history = []  # Stores (user, assistant) messages

#     def call_llm(self, prompt,
#                 num_ctx: int = 4096,
#                 temperature: float = 0.2,
#                 top_k: int = 40,
#                 top_p: float = 0.9,
#                 repeat_penalty: float = 1.2):
#         messages = []

#         if self.history_enabled and self.history:
#             messages.extend(self.history)

#         messages.append({"role": "user", "content": prompt})

#         # Use Ollama's REST API (localhost:11434 by default)
#         import requests

#         try:
#             response = requests.post(
#                 "http://localhost:11434/api/chat",
#                 json={"model": self.model_name, "messages": messages,
#                       "options": {"num_ctx": num_ctx,
#                                     "temperature": temperature,
#                                     "top_k": top_k,
#                                     "top_p": top_p,
#                                     "repeat_penalty": repeat_penalty}
#                     },
#                 stream=True
#             )
#             response.raise_for_status()
#             answer = ""
#             for line in response.iter_lines():
#                 if not line:
#                     continue
#                 try:
#                     chunk = json.loads(line)
#                     if "message" in chunk and "content" in chunk["message"]:
#                         answer += chunk["message"]["content"]
#                     else:
#                         print(f"Unexpected chunk format: {chunk}")
#                 except json.JSONDecodeError as e:
#                     print(f"JSON decode error on line: {line} — {e}")

#             if self.history_enabled:
#                 self.history.append({"role": "user", "content": prompt})
#                 self.history.append({"role": "assistant", "content": answer})

#             return answer

#         except Exception as e:
#             return f"Error communicating with LLM: {e}"
