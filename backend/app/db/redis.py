import redis.asyncio as redis

# Using redis.Redis directly automatically sets up the SSL Connection Pool correctly
redis_client = redis.Redis(
    host="amazed-jaybird-86152.upstash.io",
    port=6379,
    username="default",
    password="Zawd+1234", # Explicit password, no %2B encoding needed!
    ssl=True,
    ssl_cert_reqs="none",
    decode_responses=True
)
async def get_redis():
    """Dependency to inject Redis client if needed in API routes"""
    return redis_client
