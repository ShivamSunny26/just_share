import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Grab the MongoDB URI from our .env
MONGO_URL = os.getenv("MONGO_URL")

# Create a global async MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_URL)

db = mongo_client.just_share_db

offline_messages = db.offline_messages

# Settings up the TTL (Time-To-Live) Index
async def init_mongo_indexes():
    await offline_messages.create_index(
        "created_at", expireAfterSeconds=604800
    )