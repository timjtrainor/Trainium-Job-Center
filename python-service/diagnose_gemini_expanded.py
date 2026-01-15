import litellm
import os

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY") or api_key

models_to_test = [
    "gemini/gemini-1.5-flash",
    "gemini/gemini-1.5-flash-latest",
    "google/gemini-1.5-flash",
    "gemini-1.5-flash"
]

print(f"Testing with key starting with: {api_key[:8]}...")

for model in models_to_test:
    print(f"\n--- Testing model: {model} ---")
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            api_key=api_key,
            # Force LiteLLM to use Gemini API (Google AI Studio)
        )
        print(f"SUCCESS with {model}")
        print(f"Content: {response.choices[0].message.content}")
    except Exception as e:
        print(f"FAILURE with {model}: {type(e).__name__}: {e}")
        if hasattr(e, 'llm_response'):
             print(f"Raw Response: {e.llm_response}")
