import asyncio
import redis
import json
import os
import sys

# Add python-service to path
sys.path.insert(0, os.path.join(os.getcwd(), 'python-service'))

async def listen_for_webhooks():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))
    
    print(f"Connecting to Redis at {redis_host}:{redis_port}/{redis_db}...")
    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    pubsub = r.pubsub()
    
    channel = "job_approval_webhook"
    pubsub.subscribe(channel)
    print(f"Subscribed to '{channel}'. Waiting for messages... (Ctrl+C to stop)")
    
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                print(f"\n[RECEIVED] Channel: {message['channel']}")
                try:
                    data = json.loads(message['data'])
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    print(f"Raw data: {message['data']}")
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        pubsub.unsubscribe()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(listen_for_webhooks())
