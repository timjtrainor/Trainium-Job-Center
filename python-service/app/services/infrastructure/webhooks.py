"""
Webhook utility service for publishing events to Redis.
"""
import json
import redis
from loguru import logger
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.config import get_settings

# Global Redis connection cache
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """Get or create a cached Redis client."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=False  # Keep default for compatibility with existing code
        )
    return _redis_client

def publish_webhook_event(event_type: str, payload: Dict[str, Any], channel: Optional[str] = None):
    """
    Publish an event to a Redis channel for the webhook bridge to consume.
    
    Args:
        event_type: Type of event (e.g., 'job_approved')
        payload: Event data
        channel: Optional Redis channel name (defaults to 'job_approval_webhook')
    """
    # Use default channel if not provided
    if not channel:
        channel = "job_approval_webhook"
        
    try:
        # Get cached Redis client
        redis_conn = get_redis_client()
        
        # Prepare final payload
        webhook_payload = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload
        }
        
        # Publish to Redis
        redis_conn.publish(channel, json.dumps(webhook_payload))
        logger.info(f"Published event '{event_type}' to Redis channel '{channel}'")
        
    except Exception as e:
        logger.error(f"Failed to publish webhook event: {e}")
