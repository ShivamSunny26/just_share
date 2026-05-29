import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

# We MUST use the standard TLS connection (rediss://) for Pub/Sub, not the REST API.
UPSTASH_URL = os.getenv("UPSTASH_REDIS_URL") 

# Create the global async Redis client
redis_client = redis.from_url(UPSTASH_URL, decode_responses=True)

async def get_redis():
    """Dependency to inject Redis client if needed in API routes"""
    return redis_client
