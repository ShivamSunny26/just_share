from fastapi import FastAPI
from app.api import auth
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]


app = FastAPI(title="Just_share")

# mount the auth router under the /api/v1 prefix

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/")
async def root():
    return {
        "message": "Chat Backend is running"
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)