import uuid
from datetime import datetime, timezone
from sqlalchemy import  Column, Boolean, String, DateTime, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base
from sqlalchemy.orm import relationship



class User(Base):
    __tablename__ = "users"

    # USe UUID instead of standard integers (1,2,3) for primary key.
    # It is much more secure for public-facing chat applications.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active= Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    

    # Link to tokens
    tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")

    sent_requests = relationship("Friendship", foreign_keys="[Friendship.requester_id]", back_populates="requester", cascade="all, delete-orphan")
    received_requests = relationship("Friendship", foreign_keys="[Friendship.addressee_id]", back_populates="addressee", cascade="all, delete-orphan")

class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String,unique=True, index=True, nullable=False)
    token_type= Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="tokens")
