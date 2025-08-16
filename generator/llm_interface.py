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
    def __init__(self, model_name="gemini-2.5-flash-lite", history_enabled=False, client=client):
        self.model_name = model_name
        self.history_enabled = history_enabled
        self.history = ""

    def call_llm(self, prompt):
        

        if self.history_enabled and self.history:
            self.history += f"User: {prompt}\nAssistant: "
        else:
            self.history = f"User: {prompt}\nAssistant: "


        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=self.history,
            )

            if self.history_enabled:
                self.history += response.text + "\n"

            return response.text if response else "No response from LLM"

        except Exception as e:
            return f"Error communicating with LLM: {e}"

