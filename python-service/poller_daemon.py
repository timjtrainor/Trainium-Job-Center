#!/usr/bin/env python3
"""
Poller daemon script.
Runs the job poller service in a loop to check for pending review jobs and enqueue them.
"""
import sys
import os
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from app.core.config import get_settings, configure_logging
from app.services.infrastructure.poller import get_poller_service


async def poller_loop():
    """Main poller loop."""
    
    configure_logging()
    settings = get_settings()
    
    logger.info("Starting poller daemon...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Poll interval: {settings.poll_interval_minutes} minutes")
    
    poller_service = get_poller_service()
    
    try:
        # Initialize poller
        await poller_service.initialize()
        
        if not poller_service.initialized:
            logger.error("Failed to initialize poller service")
            return
            
        logger.info("Poller daemon initialized successfully")
        
        # Start the continuous polling loop
        await poller_service.start_polling_loop()
        
    except KeyboardInterrupt:
        logger.info("Poller daemon interrupted by user")
    except Exception as e:
        logger.error(f"Poller daemon failed: {str(e)}")
        raise


def main():
    """Entry point for poller daemon."""
    try:
        asyncio.run(poller_loop())
    except KeyboardInterrupt:
        logger.info("Poller daemon stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Poller daemon error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()