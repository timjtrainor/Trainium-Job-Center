import os
import sys
from loguru import logger

# Add app to path
sys.path.append("/app")

from app.services.ai.ai_service import ai_service

def test_prompt_association():
    prompt_name = "COMPANY_GOAL_ANALYSIS"
    variables = {"company_name": "TestCorp", "raw_content": "Our goal is to win."}
    
    logger.info(f"Executing prompt: {prompt_name}")
    try:
        result = ai_service.execute_prompt(
            prompt_name=prompt_name,
            variables=variables,
            trace_source="association_test"
        )
        logger.info(f"Execution successful. Result type: {type(result)}")
    except Exception as e:
        logger.error(f"Execution failed: {e}")

if __name__ == "__main__":
    test_prompt_association()
