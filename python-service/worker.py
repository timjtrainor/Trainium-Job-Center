#!/usr/bin/env python3
"""
RQ Worker startup script.
Run this script to start worker processes that consume jobs from the Redis queue.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rq import Worker, Connection
import redis
from loguru import logger

from app.core.config import get_settings, configure_logging


def main():
    """Start RQ worker processes."""
    
    # Configure logging
    configure_logging()
    settings = get_settings()
    
    logger.info("Starting RQ worker...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
    logger.info(f"Queue: {settings.rq_queue_name}")
    
    try:
        # Connect to Redis
        redis_conn = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
        )
        
        # Test connection
        redis_conn.ping()
        logger.info("Redis connection established")
        
        # Create and start worker
        with Connection(redis_conn):
            worker = Worker([settings.rq_queue_name])
            logger.info(f"Worker started for queue: {settings.rq_queue_name}")
            worker.work()
            
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed to start: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
