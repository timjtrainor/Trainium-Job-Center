
import os
import sys
import re
import hashlib
from typing import Dict, Any, List
from loguru import logger
from langfuse import Langfuse

# Add project root to path
# This handles imports for app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env vars from root .env
from dotenv import load_dotenv
root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(root_env)

# Initialize Langfuse
# Relies on env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
langfuse = Langfuse()

def parse_prompts_data(file_path: str) -> List[Dict[str, str]]:
    """
    Parses promptsData.ts and extracts id, name, description, and content.
    Uses regex to handle the TypeScript object format.
    """
    if not os.path.exists(file_path):
        logger.error(f"Could not find prompts file at {file_path}")
        return []

    with open(file_path, 'r') as f:
        content = f.read()
    
    # regex for objects in the PROMPTS array
    # id, name, description use either ' or "
    # content uses ` and can contain escaped backticks \`
    pattern = re.compile(
        r'\{\s*id:\s*(?P<q1>[\'"])(?P<id>.*?)(?P=q1),\s*'
        r'name:\s*(?P<q2>[\'"])(?P<name>.*?)(?P=q2),\s*'
        r'description:\s*(?P<q3>[\'"])(?P<description>.*?)(?P=q3),\s*'
        r'content:\s*`(?P<content>.*?)`',
        # Note: we don't strictly require the closing brace here to be the very next thing 
        # in case of trailing commas or other fields, but we do need re.DOTALL
        re.DOTALL
    )
    
    prompts = []
    for match in pattern.finditer(content):
        d = match.groupdict()
        res = {
            'id': d['id'],
            'name': d['name'],
            'description': d['description'],
            'content': d['content'].replace(r'\`', '`').strip()
        }
        prompts.append(res)
    return prompts

def migrate_ui_prompts():
    """Migrates UI prompts from promptsData.ts to LangFuse."""
    
    # Try different locations for promptsData.ts
    possible_paths = [
        "../promptsData.ts",      # If running from python-service/scripts/
        "promptsData.ts",         # If running from project root
        "../../promptsData.ts",   # If running from deeper in python-service
    ]
    
    ts_path = None
    for path in possible_paths:
        if os.path.exists(path):
            ts_path = path
            break
            
    if not ts_path:
        logger.error("Could not find promptsData.ts in any expected location.")
        return

    logger.info(f"Using prompts source: {ts_path}")
    prompts = parse_prompts_data(ts_path)
    logger.info(f"Found {len(prompts)} UI prompts to migrate.")

    count = 0
    skipped = 0
    
    for p in prompts:
        prompt_name = p['id']
        prompt_text = p['content']
        
        # Default configuration for UI prompts
        # We use strategic aliases from model_config.yaml
        config = {
            "model": "fast-response", 
            "temperature": 0.3,
            "description": p['description'], # Metadata in config
            "friendly_name": p['name']
        }
        
        # IDEMPOTENCY CHECK
        should_update = True
        try:
            # Get current production version
            existing_prompt = langfuse.get_prompt(prompt_name, label="production")
            
            # Simple check: identical content and config
            # We compare the raw prompt text and the config dictionary
            if existing_prompt.prompt == prompt_text and existing_prompt.config == config:
                should_update = False
                logger.debug(f"Skipping {prompt_name} - no changes detected.")
                skipped += 1
        except Exception:
            # Prompt doesn't exist or other error -> Create/Update it
            should_update = True

        if should_update:
            logger.info(f"Creating/Updating prompt: {prompt_name}")
            try:
                langfuse.create_prompt(
                    name=prompt_name,
                    prompt=prompt_text,
                    config=config,
                    labels=["production"],
                    tags=["ui-prompt", "auto-migrated"]
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to migrate {prompt_name}: {e}")

    logger.success(f"UI Prompt Migration complete. Created/Updated: {count}, Skipped: {skipped}")

if __name__ == "__main__":
    migrate_ui_prompts()
