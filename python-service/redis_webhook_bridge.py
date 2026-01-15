#!/usr/bin/env python3
"""
Dynamic Redis-to-Webhook Bridge Service.
Queries database for webhook configurations and routes Redis messages to multiple 
configured destinations. Supports hot-reloading of configurations.
"""
import sys
import os
import asyncio
import json
import httpx
from redis.asyncio import Redis
from loguru import logger
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings, configure_logging
from app.services.infrastructure.database import get_database_service

class WebhookRouter:
    def __init__(self):
        self.settings = get_settings()
        self.db = get_database_service()
        self.routes = {} # Map of channel -> list of config dicts
        self.last_refresh = None
        self.refresh_interval = 60 # seconds
        self.redis = None
        self.pubsub = None
        self.subscribed_channels = set()

    async def initialize(self):
        """Initialize DB and Redis connections."""
        configure_logging()
        await self.db.initialize()
        
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis = Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        
        logger.info(f"Router initialized. Redis: {redis_host}:{redis_port}/{redis_db}")

    async def fetch_configs(self):
        """Fetch active webhook configurations from database."""
        try:
            query = """
            SELECT name, redis_channel, webhook_url, auth_token 
            FROM public.webhook_configurations 
            WHERE active = true
            """
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch(query)
            
            new_routes = {}
            for row in rows:
                channel = row['redis_channel']
                if channel not in new_routes:
                    new_routes[channel] = []
                new_routes[channel].append(dict(row))
            
            self.routes = new_routes
            self.last_refresh = datetime.now(timezone.utc)
            
            # Update subscriptions
            new_channels = set(self.routes.keys())
            
            # Legacy fallback if no DB configs exist (using env)
            env_channel = os.getenv("REDIS_CHANNEL", "job_review_webhook")
            env_url = os.getenv("WEB_HOOK_URL")
            if env_url and env_channel not in new_channels:
                if env_channel not in self.routes:
                    self.routes[env_channel] = []
                self.routes[env_channel].append({
                    "name": "Legacy Env Webhook",
                    "webhook_url": env_url,
                    "auth_token": os.getenv("WEBHOOK_API_KEY")
                })
                new_channels.add(env_channel)

            channels_to_add = new_channels - self.subscribed_channels
            channels_to_remove = self.subscribed_channels - new_channels

            if channels_to_add:
                await self.pubsub.subscribe(*channels_to_add)
                logger.info(f"Subscribed to new channels: {channels_to_add}")
            
            if channels_to_remove:
                await self.pubsub.unsubscribe(*channels_to_remove)
                logger.info(f"Unsubscribed from channels: {channels_to_remove}")

            self.subscribed_channels = new_channels
            logger.info(f"Refreshed {len(rows)} webhook configurations across {len(self.routes)} channels.")
            
        except Exception as e:
            logger.error(f"Failed to fetch webhook configs: {e}")

    async def forward_to_webhook(self, client, config, payload):
        """Forward payload to a specific webhook."""
        name = config.get('name', 'Unknown')
        url = config.get('webhook_url')
        token = config.get('auth_token')
        
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            logger.info(f"Forwarding to '{name}' at {url}...")
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            
            if response.is_success:
                logger.success(f"Successfully forwarded to '{name}': {response.status_code}")
            else:
                logger.error(f"Error from '{name}' ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Failed to forward to '{name}': {e}")

    async def run(self):
        """Main execution loop."""
        await self.initialize()
        await self.fetch_configs()
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    # Check if refresh needed
                    if not self.last_refresh or (datetime.now(timezone.utc) - self.last_refresh).total_seconds() > self.refresh_interval:
                        await self.fetch_configs()

                    # Check for messages
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message:
                        channel = message.get("channel")
                        payload_str = message.get("data")
                        
                        logger.info(f"Received message on channel '{channel}'")
                        
                        try:
                            payload = json.loads(payload_str)
                            configs = self.routes.get(channel, [])
                            
                            if configs:
                                tasks = [self.forward_to_webhook(client, cfg, payload) for cfg in configs]
                                await asyncio.gather(*tasks)
                            else:
                                logger.warning(f"No active webhooks configured for channel '{channel}'")
                                
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode message on '{channel}': {payload_str[:100]}...")
                    
                    await asyncio.sleep(0.01)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in router loop: {e}")
                    await asyncio.sleep(5)

async def main():
    router = WebhookRouter()
    try:
        await router.run()
    except KeyboardInterrupt:
        logger.info("Router stopped by user")
    except Exception as e:
        logger.critical(f"Router failure: {e}")

if __name__ == "__main__":
    asyncio.run(main())
