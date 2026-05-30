from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, friend, chat, users
from app.db.mongo import init_mongo_indexes

# --- NEW POSTGRES DATABASE IMPORTS ---
from app.db.postgres import engine, Base

from app.models.user import User, VerificationToken
from app.models.friend import Friendship


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Just_share backend...")
    
    try:
        async with engine.begin() as conn:
            # This scans your imported models and creates any missing tables automatically
            await conn.run_sync(Base.metadata.create_all)
        print("PostgreSQL tables verified/created successfully.")
    except Exception as e:
        print(f"Warning: PostgreSQL table creation failed: {e}")

    # 2. Initialize MongoDB TTL indexes
    try:
        await init_mongo_indexes()
        print("MongoDB TTL indexes initialized.")
    except Exception as e:
        print(f"Warning: MongoDB indexes failed: {e}")
        
    yield 
    
    print("Shutting down Just_share backend...")


app = FastAPI(title="Just_share", lifespan=lifespan)

origins=[
    "http://localhost:5173",
]
# CORS configuration to allow local network testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registering your API Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(friend.router, prefix="/api/v1/friends", tags=["Friends"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

@app.get("/")
async def root():
    return {"message": "Chat Backend is running. Ephemeral messaging active."}