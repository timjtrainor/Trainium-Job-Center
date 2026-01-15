import os
import time
from langfuse import get_client
from loguru import logger

def test_connectivity():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    logger.info(f"Testing Langfuse connectivity to {host}")
    logger.info(f"Public Key: {public_key[:8]}...")
    
    langfuse = get_client()
    
    logger.info(f"Authenticating...")
    try:
        if langfuse.auth_check():
            logger.info("Authentication SUCCESSful!")
        else:
            logger.error("Authentication FAILED! Check keys.")
            return
    except Exception as e:
        logger.error(f"Auth check exploded: {e}")
        return

    logger.info("Starting observation...")
    with langfuse.start_as_current_observation(
        as_type="generation", 
        name="Connectivity Test v3", 
        model="gpt-3.5-turbo"
    ) as generation:
        logger.info(f"In observation context. Generation ID potential: {langfuse.get_current_observation_id()}")
        generation.update(
            input="Hello Langfuse v3 Quickstart", 
            output="Tracing is active!"
        )
    
    logger.info("Flushing...")
    langfuse.flush()
    logger.info("Flush complete. Check Langfuse UI.")

if __name__ == "__main__":
    test_connectivity()
