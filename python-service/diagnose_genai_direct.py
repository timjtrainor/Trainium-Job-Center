from google import genai
import os
import json

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")

print(f"Testing with key starting with: {api_key[:8]}...")

# Use the model from the user's dashboard
model_name = 'gemini-3-flash-preview'

client = genai.Client(api_key=api_key)

print(f"\n--- Testing direct Google GenAI SDK with {model_name} ---")
try:
    response = client.models.generate_content(
        model=model_name,
        contents="Ready?"
    )
    print("SUCCESS!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
    # Inspect 429 details if possible
    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        print("Confirmed: Quota exhaustion or Rate Limit hit on Google AI Studio.")
