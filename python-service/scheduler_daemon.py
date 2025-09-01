#!/usr/bin/env python3
"""
Scheduler daemon script.
Runs the job scheduling logic in a loop to enqueue periodic scraping tasks.
"""
import sys
import os
import asyncio
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from app.core.config import get_settings, configure_logging
from app.services.scheduler import get_scheduler_service


async def scheduler_loop():
    """Main scheduler loop."""
    
    configure_logging()
    settings = get_settings()
    
    logger.info("Starting scheduler daemon...")
    logger.info(f"Environment: {settings.environment}")
    
    scheduler_service = get_scheduler_service()
    
    try:
        # Initialize scheduler
        await scheduler_service.initialize()
        logger.info("Scheduler initialized successfully")
        
        # Run scheduler loop
        check_interval = 60  # Check every minute
        
        while True:
            try:
                logger.debug("Checking for due scheduled tasks...")
                jobs_enqueued = await scheduler_service.process_scheduled_sites()
                
                if jobs_enqueued > 0:
                    logger.info(f"Scheduler enqueued {jobs_enqueued} tasks")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                # Wait a bit longer before retrying
                await asyncio.sleep(check_interval * 2)
                
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler daemon failed: {str(e)}")
        raise


def main():
    """Entry point for scheduler daemon."""
    try:
        asyncio.run(scheduler_loop())
    except KeyboardInterrupt:
        logger.info("Scheduler daemon stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler daemon error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()