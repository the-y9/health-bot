# generator/llm_interface.py
import json
import requests

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

client = genai.Client(api_key=API_KEY)

class LLMInterface:
    def __init__(self, model_name="gemini-2.5-flash-lite", history=False, client=client):
        self.model_name = model_name
        self.history_enabled = history
        self.history = []

    def call_llm(self, prompt,
                num_ctx: int = 4096,
                temperature: float = 0.2,
                top_k: int = 40,
                top_p: float = 0.9,
                repeat_penalty: float = 1.2):
        messages = []

        if self.history_enabled and self.history:
            messages.extend(self.history)

        messages.append({"role": "user", "content": prompt})

        try:
            response = client.models.generate_content(model="gemini-2.5-flash-lite", 
                                                      contents=prompt,
                                                      )
            # response = requests.post(
            #     "http://localhost:11434/api/chat",
            #     json={"model": self.model_name, "messages": messages,
            #           "options": {"num_ctx": num_ctx,
            #                         "temperature": temperature,
            #                         "top_k": top_k,
            #                         "top_p": top_p,
            #                         "repeat_penalty": repeat_penalty}
            #         },
            #     stream=True
            # )
            # response.raise_for_status()
            # answer = ""
            # for line in response.iter_lines():
            #     if not line:
            #         continue
            #     try:
            #         chunk = json.loads(line)
            #         if "message" in chunk and "content" in chunk["message"]:
            #             answer += chunk["message"]["content"]
            #         else:
            #             print(f"Unexpected chunk format: {chunk}")
            #     except json.JSONDecodeError as e:
            #         print(f"JSON decode error on line: {line} — {e}")

            # if self.history_enabled:
            #     self.history.append({"role": "user", "content": prompt})
            #     self.history.append({"role": "assistant", "content": answer})

            return response.text if response else "No response from LLM"

        except Exception as e:
            return f"Error communicating with LLM: {e}"
