import os
import sys
import time
from dotenv import load_dotenv
from langfuse import Langfuse
import litellm

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_dir, ".."))
dotenv_path = os.path.join(root_path, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Disable Auto-Callback (The Fix)
litellm.success_callback = []
litellm.failure_callback = []

def verify():
    print("\n=== VERIFICATION PROTOCOL (V2 - Manual Tracing) ===")
    
    # 1. Langfuse Init
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    if not public_key or not host:
        print("❌ Missing Langfuse credentials.")
        return

    print(f"Connecting to Langfuse Host: {host}")
    langfuse = Langfuse(debug=False)
    
    # 2. Manual Tracing Workflow
    prompt_name = "company/web-research"
    
    # Mocking the AI Service logic inline to verify it runs without crashing
    try:
        print(f"Starting Trace for '{prompt_name}'...")
        
        with langfuse.start_as_current_observation(
            name=f"verify_{prompt_name}",
            as_type="generation",
            model="gpt-3.5-turbo (mock)",
            input=[{"role": "user", "content": "Ping"}]
        ) as generation:
            
            # 2.1 Fetch Prompt (Check Connectivity)
            try:
                prompt = langfuse.get_prompt(prompt_name)
                print(f"✅ Fetch Prompt Success: {prompt.name}")
            except Exception as e:
                print(f"⚠️ Fetch Prompt Failed (Expected if prompt missing): {e}")

            # 2.2 Simulate LiteLLM Call (No auto-callback)
            if os.getenv("OPENAI_API_KEY"):
                print("Sending request to LiteLLM (gpt-3.5-turbo)...")
                response = litellm.completion(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Ping verification."}]
                )
                print(f"✅ LiteLLM Completion Success: {response.choices[0].message.content}")
                
                # 2.3 Manual Update
                generation.update(
                    output=response.choices[0].message.content,
                    usage_details={"input": 1, "output": 1, "total": 2}
                )
                print("✅ Manual Trace Update Success")
            else:
                print("⚠️ No OPENAI_API_KEY. Skipping real LLM call.")

        langfuse.flush()
        print("✅ Langfuse Flushed (No crash).")

    except Exception as e:
        print(f"❌ Verification Logic Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    verify()
