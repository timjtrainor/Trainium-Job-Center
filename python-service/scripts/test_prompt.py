import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Ensure we can import from the app
sys.path.append(os.getcwd())

from app.services.ai.ai_service import ai_service

def run_test(prompt_name, variables_str, model_alias=None, user_id="test-user"):
    """
    Runs a full execution cycle for a given prompt name and variables.
    """
    print(f"\n--- AI PROMPT TEST HARNESS ---")
    print(f"Prompt: {prompt_name}")
    if model_alias:
        print(f"Model Override: {model_alias}")
    
    try:
        variables = json.loads(variables_str) if variables_str else {}
    except json.JSONDecodeError:
        print(f"❌ Error: Variables must be valid JSON string.")
        return

    print(f"Variables: {json.dumps(variables, indent=2)}")
    print(f"Running...")

    try:
        # Load .env manually if needed
        load_dotenv(".env")
        
        result = ai_service.execute_prompt(
            prompt_name=prompt_name,
            variables=variables,
            model_alias=model_alias,
            user_id=user_id,
            label="production"
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Result Type: {type(result)}")
        
        if isinstance(result, dict):
            print("Result (JSON):")
            print(json.dumps(result, indent=2))
        else:
            print("Result (Text):")
            print(result)
            
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test any Langfuse prompt via AIService")
    parser.add_argument("prompt", help="Name of the prompt in Langfuse")
    parser.add_argument("--vars", help="JSON string of variables", default="{}")
    parser.add_argument("--model", help="Model alias override", default=None)
    parser.add_argument("--user", help="User ID for tracing", default="test-harness-user")
    
    args = parser.parse_args()
    
    # Run test
    run_test(args.prompt, args.vars, args.model, args.user)
