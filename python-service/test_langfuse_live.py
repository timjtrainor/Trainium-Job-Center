import os
import time
from langfuse import get_client
from loguru import logger

def test_connectivity():
    langfuse = get_client()
    logger.info("Starting observation for LIVE TEST...")
    with langfuse.start_as_current_observation(
        as_type="generation", 
        name=f"Live Test {int(time.time())}", 
        model="gpt-3.5-turbo"
    ) as generation:
        generation.update(
            input="Checking real-time ingestion", 
            output="Injected!"
        )
    langfuse.flush()
    logger.info("Flush complete.")

if __name__ == "__main__":
    test_connectivity()
