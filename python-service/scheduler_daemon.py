#!/usr/bin/env python3
"""
Enhanced scheduler daemon script.
Runs the job scheduling logic in a loop to enqueue periodic scraping tasks.
Features improved reliability, diagnostics, and error handling.
"""
import sys
import os
import asyncio
import time
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from app.core.config import get_settings, configure_logging
from app.services.infrastructure.scheduler import get_scheduler_service


async def scheduler_loop():
    """Main scheduler loop with enhanced reliability and diagnostics."""
    
    configure_logging()
    settings = get_settings()
    
    logger.info("🚀 Starting enhanced scheduler daemon...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url[:50]}...")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
    logger.info(f"Queue: {settings.rq_queue_name}")
    
    scheduler_service = get_scheduler_service()
    
    try:
        # Initialize scheduler with connectivity checks
        logger.info("🔧 Initializing scheduler services...")
        init_success = await scheduler_service.initialize()
        
        if not init_success:
            logger.error("❌ Failed to initialize scheduler - check database and Redis connectivity")
            return
        
        logger.info("✅ Scheduler initialized successfully")
        
        # Run initial status check
        status = await scheduler_service.get_scheduler_status()
        logger.info(f"📊 Initial status: {status}")
        
        # Run scheduler loop with health monitoring
        check_interval = 60  # Check every minute
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        logger.info(f"⏰ Starting scheduler loop (check interval: {check_interval}s)")
        
        while True:
            try:
                loop_start = datetime.now(timezone.utc)
                logger.debug(f"🔍 Checking for due scheduled tasks at {loop_start.isoformat()}")
                
                jobs_enqueued = await scheduler_service.process_scheduled_sites()
                
                if jobs_enqueued > 0:
                    logger.info(f"📈 Scheduler cycle complete - enqueued {jobs_enqueued} tasks")
                    consecutive_failures = 0  # Reset failure counter on success
                else:
                    logger.debug("⏸️ Scheduler cycle complete - no jobs due")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"💥 Error in scheduler loop (failure #{consecutive_failures}): {str(e)}")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical(f"🆘 Scheduler has failed {consecutive_failures} consecutive times - stopping")
                    break
                
                # Wait longer before retrying after errors
                error_wait = min(check_interval * consecutive_failures, 300)  # Max 5 min
                logger.info(f"⏳ Waiting {error_wait}s before retry...")
                await asyncio.sleep(error_wait)
                
    except KeyboardInterrupt:
        logger.info("⛔ Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"💥 Scheduler daemon failed with critical error: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("🧹 Scheduler daemon shutting down...")


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