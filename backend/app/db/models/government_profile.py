from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class GovernmentProfile(Base):
    __tablename__ = "government_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    organization_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    official_email = Column(String, nullable=False)
    official_phone = Column(String, nullable=False)
    jurisdiction = Column(String, default="Greater Mumbai (All Wards)", nullable=False)
    verification_status = Column(String, default="PENDING", nullable=False) # PENDING, VERIFIED, SUSPENDED
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    invitation_token = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="government_profile")
