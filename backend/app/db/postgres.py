import os
import ssl
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base


load_dotenv()

# We must replac standard "postgresql://" with "postgresql+asyncpg://"
# so SQLAlchemy knows to us  the asunchronous drive for FastAPI WebSockets.

RAW_URL = os.getenv("SUPABASE_DATABASE_URL")
ASYNC_DB_URL =RAW_URL.replace("postgresql://", "postgresql+asyncpg://")


# Create a custom SSL content
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE 

# Create the async engine with connection pooling enabled
engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"ssl": ssl_context}
)

# The async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# The base class all your model will inherit from
Base = declarative_base()

# Dependency block to inject database sessions into yout FastAPI routes safely
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()