import litellm
import os

# Turn on debug logging
litellm.set_verbose = True

# Pick up key from environment
api_key = os.getenv("GEMINI_API_KEY")

print(f"Testing with key starting with: {api_key[:8]}...")

# We'll test with the model the user says they are using
model = "gemini/gemini-1.5-flash" # or gemini-3-flash if it exists in the registry

print(f"\n--- Debugging LiteLLM routing for {model} ---")
try:
    # This should show the URL and payload in the console
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": "hi"}],
        api_key=api_key
    )
    print("\nSUCCESS!")
except Exception as e:
    print(f"\nFAILURE: {type(e).__name__}")
    if hasattr(e, 'llm_response'):
        print(f"Raw Response: {e.llm_response}")
    else:
        print(f"Error Message: {str(e)}")
