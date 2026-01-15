from google import genai
import os

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print(f"Testing with key starting with: {api_key[:8]}...")

print("\n--- Listing available models ---")
try:
    for model in client.models.list():
        print(f"Model Name: {model.name}, Display Name: {model.display_name}")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
