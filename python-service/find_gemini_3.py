from google import genai
import os

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    models = list(client.models.list())
    gemini_3_models = [m for m in models if "gemini-3" in m.name.lower()]
    print(f"Found {len(gemini_3_models)} Gemini 3 models:")
    for m in gemini_3_models:
        print(f"ID: {m.name}, Display: {m.display_name}")
    
    if not gemini_3_models:
        print("\nNo Gemini 3 models found. Showing all Gemini models:")
        gemini_models = [m for m in models if "gemini" in m.name.lower()]
        for m in gemini_models:
            print(f"ID: {m.name}, Display: {m.display_name}")

except Exception as e:
    print(f"FAILURE: {e}")
