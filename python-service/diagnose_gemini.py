import litellm
import os
from loguru import logger

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")
model = "gemini/gemini-1.5-flash" # Use a stable model first

print(f"Testing with key starting with: {api_key[:8]}...")

try:
    print(f"Attempting completion with {model}...")
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": "Hello, are you there? Please respond with 'Ready' if you are up."}],
        api_key=api_key
    )
    print("Success!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
    # Print more details if it's a RateLimitError
    if hasattr(e, 'llm_response'):
        print(f"LLM Response: {e.llm_response}")
