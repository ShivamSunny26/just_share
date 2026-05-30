import uuid
from datetime import datetime, timezone
from sqlalchemy import  Column, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base
from sqlalchemy.orm import relationship
import enum

class FriendshipStatus(str, enum.Enum):
    PENDING =   "PENDING"
    ACCEPTED =  "ACCEPTED"
    BLOCKED =   "BLOCKED"


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    addressee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(FriendshipStatus), default=FriendshipStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendship_request"),
    )

    requester = relationship("User", foreign_keys="Friendship.requester_id", lazy="selectin")
    addressee = relationship("User", foreign_keys="Friendship.addressee_id", lazy="selectin")