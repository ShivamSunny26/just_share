from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from uuid import UUID
import jwt

from app.services.socket_manager import manager
from app.core.jwt import SECRET_KEY, ALGORITHM

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
            
            # Expected incoming JSON: {"receiver_id": "uuid-string", "content": "hello"}
            receiver_id_str = data.get("receiver_id")
            content = data.get("content")
            
            if receiver_id_str and content:
                receiver_id = UUID(receiver_id_str)
                
                # Format the payload for the recipient
                payload_to_send = {
                    "sender_id": str(user_id),
                    "content": content,
                }
                
                # Handoff to the router to either send immediately or encrypt & save
                await manager.route_message(payload_to_send, receiver_id, sender_id=user_id)

    except WebSocketDisconnect:
        # 4. Gracefully disconnect when the user closes the app/browser
        await manager.disconnect(user_id)