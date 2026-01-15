import litellm
import os

# Set debug via environment variable as recommended by LiteLLM warning
os.environ['LITELLM_LOG'] = 'DEBUG'

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")
model = "gemini/gemini-3-flash-preview"

print(f"Testing with key starting with: {api_key[:8]}...")

print(f"\n--- Testing LiteLLM with {model} ---")
try:
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": "test"}],
        api_key=api_key
    )
    print("\nSUCCESS!")
except Exception as e:
    print(f"\nFAILURE: {type(e).__name__}")
    if hasattr(e, 'llm_response'):
        print(f"Raw Response Body: {e.llm_response}")
    else:
        print(f"Error Message: {str(e)}")
