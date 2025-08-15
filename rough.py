from google import genai
from dotenv import load_dotenv
import os
import time

start = time.time()
load_dotenv()
API_KEY = os.getenv("API_KEY")


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash-lite", contents="Explain how AI works in a few words"
)
print(response.text)
end = time.time()
print(f"Time taken: {end - start} seconds")