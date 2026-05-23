import uuid
from datetime import datetime, timezone
from sqlalchemy import  Column, Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class User(Base):
    __tablename__ = "users"

    # USe UUID instead of standard integers (1,2,3) for primary key.
    # It is much more secure for public-facing chat applications.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    hashed_password = Column(String, default=True)

    is_active= Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id_1 = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id_2 = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Track the relationship status (e.g., 'pending', 'accepted', 'blocked')

    status = Column(String, default="pending")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))