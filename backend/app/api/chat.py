from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import jwt

from app.services.socket_manager import manager
from app.core.jwt import SECRET_KEY, ALGORITHM
from app.db.postgres import get_db
from app.api.deps import get_current_user_id
from app.crud import user as user_crud
from app.schemas import user as user_schemas
from app.db.redis import redis_client

router = APIRouter()

async def authenticate_ws(token: str) -> UUID | None:
    """Helper to validate JWT from WebSocket query parameters."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        token_type = payload.get("type")
        
        if user_id_str is None or token_type != "access":
            return None
        return UUID(user_id_str)
    except Exception as e:
        print(f"WebSocket Auth Error: {e}")
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    Main WebSocket connection endpoint.
    Client connects via: ws://<YOUR_LOCAL_IP>:8000/api/v1/chat/ws?token=<ACCESS_TOKEN>
    """
    # 1. Authenticate the connection using the query token
    user_id = await authenticate_ws(token)
    if not user_id:
        # Close connection with HTTP 1008 Policy Violation if token is invalid
        await websocket.close(code=1008) 
        return

    # 2. Register the connection with our socket manager
    await manager.connect(websocket, user_id)

    try:
        # 3. Infinite loop to listen for incoming messages
        while True:
            data = await websocket.receive_json()
            
            event_type = data.get("type", "chat_message")
            receiver_id_str = data.get("receiver_id")

            if not receiver_id_str:
                continue
            
            receiver_id = UUID(receiver_id_str)

            # --- ROUTING LOGIC BASED ON EVENT TYPE ---
            if event_type == "chat_message":
                content = data.get("content")
                if content:
                    payload_to_send = {
                        "type": "chat_message",
                        "sender_id": str(user_id),
                        "content": content
                    }
                    # Route message: Send if online, encrypts & saves to Mongo if offline
                    await manager.route_message(payload_to_send, receiver_id, sender_id=user_id)

            elif event_type == "typing":
                payload_to_send = {
                    "type": "typing",
                    "sender_id": str(user_id)
                }
                # Send personal message ONLY if they are online. NEVER save this to Mongo
                await manager.send_personal_message(payload_to_send, receiver_id)
            elif event_type == "read_receipt":
                message_id = data.get("message_id")
                payload_to_send = {
                    "type": "read_receipt",
                    "sender_id": str(user_id),
                    "messsage_id": message_id
                }
                # Forward the read receipt so the sender's UI shows "Opened"
                await manager.send_personal_message(payload_to_send, receiver_id)
        
    except WebSocketDisconnect:
        # 4. Gracefully diconnect when the user closes the app/browser
        await manager.disconnect(user_id)



# --- HTTP ENDPOINT FOR CHAT UI ---
@router.get("/contacts", response_model=List[user_schemas.UserSearchResponse])
async def get_home_screen_contacts(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Return a List of users"""
    contacts = await user_crud.get_chat_contacts(db, current_user_id)

    for contact in contacts:
        contact.friendship_status = "accepted"

    return contacts

@router.get("/presence", response_model=dict)
async def get_fridends_presence(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Checks Redis to see which of the user's friend are currently
    """
    # 1. Get the accepted friends list
    contacts = await user_crud.get_chat_contacts(db, current_user_id)

    if not contacts:
        return {}

    # 2. Build a list of Redis keys to check for these specific friends
    redis_keys = [f"user:online: {str(contacts.id)}" for contact in contacts]

    # 3. Use Redis MGET (Multi-Get) to fetch all statuses in One lightning-fast query
    redis_results = await redis_client.mget(redis_keys)

    # 4. Format the output into a dictionary for the frontend
    presence_dict = {}
    for contact, is_online in zip(contacts, redis_results):
        presence_dict[str(contact.id)] = (is_online == "true")
    return presence_dict
    