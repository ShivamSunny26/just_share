from fastapi import WebSocket
from uuid import UUID
import json
from datetime import datetime, timezone

from app.db.redis import redis_client 
from app.db.mongo import offline_messages
# from app.core.encryption import playfair_encrypt, playfair_decrypt

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        """Accepts the connection and stores it in memory."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # 1. Update global presence in Upstash Redis (set to expire in 24 hours)
        redis_key = f'user:online:{str(user_id)}'
        await redis_client.set(redis_key, "true", ex=86400)

        print(f"User {user_id} connected. Total online: {len(self.active_connections)}")

        # 2. Fetch any offline messages waiting in MongoDB Atlas
        await self.deliver_offline_messages(websocket, user_id)

    async def disconnect(self, user_id: UUID):
        """Remove the connection from memory."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected.")
        
        # Remove global presence from Redis
        redis_key = f"user:online: {str(user_id)}"
        await redis_client.delete(redis_key)

    async def route_message(self, payload: dict, receiver_id: UUID, sender_id: UUID):
        """Local Router: Checks memory first. If not there, saves to Mongo"""
        # 1. USer is online (In memory) :Route instantly via WebSocket
        if receiver_id in self.active_connections:
            ws = self.active_connections[receiver_id]
            await ws.send_json(payload)
            print(f"Message instatly delivered to {receiver_id}")
            return
        
        # encrypted_content = playfair_encrypt(payload["content"], "SECRET")

        offline_doc = {
            "sender_id": str(sender_id),
            "receiver_id": str(receiver_id),
            "content": payload["content"],
            "created_at": datetime.now(timezone.utc)
        }
        await offline_messages.insert_one(offline_doc)
        print(f"User {receiver_id} is offline. Message encrypted and saved to MongoDB")


    async def deliver_offline_messages(self, websocket: WebSocket, user_id: UUID):
        """Fetcches, sends, and wipes offline messages"""
        cursor = offline_messages.find({"receiver_id": str(user_id)})
        messages_sent = 0
        docs = await cursor.to_list(length=100)

        for doc in docs:
            payload = {
                "type": "chat_message",
                "sender_id": doc["sender_id"],
                "content": doc["content"],
                "timestamp": doc["created_at"].isoformat()
            }
            await websocket.send_json(payload)
            messages_sent += 1

        if messages_sent > 0:
            await offline_messages.delete_many({"receiver_id": str(user_id)})
            print(f"Delivered and wiped {messages_sent} offline messages for {user_id}")

    async def send_personal_message(self, message: dict, receiver_id: UUID) -> bool:
        """
        Attempts to send a message to a sepcific user.
        Returns True if delivered, False if the user is offline
        """
        if receiver_id in self.active_connections:
            websocket = self.active_connections[receiver_id]
            await websocket.send_json(message)
            return True
        
        return False
    

    async def is_user_online_globally(self, user_id: UUID) -> bool:
        """Checks Updatash Redis to see if the use is connected to ANY server instance."""
        redis_key = f"user:online:{str(user_id)}"
        result = await redis_client.get(redis_key)
        return result == "true"
    
manager = ConnectionManager()