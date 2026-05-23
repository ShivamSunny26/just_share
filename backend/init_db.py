import asyncio
from app.db.postgres import engine, Base

# We must import our models here so SQLAlchemy know they exist 
# before it tries to build the tables.
from app.models.user import User, Friendship

async def create_tables():
    print("Connecting to Supabase to create tables....")
    # Open an async connection
    async with engine.begin() as conn:
        # Run the synchronous create_all command inside the async connection
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())