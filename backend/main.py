from fastapi import FastAPI
from app.api import auth

app = FastAPI(title="Just_share")

# mount the auth router under the /api/v1 prefix

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/")
async def root():
    return {
        "message": "Chat Backend is running"
    }