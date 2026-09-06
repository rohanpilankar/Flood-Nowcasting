from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.db.base import Base

class OtpVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    target = Column(String, index=True, nullable=False) # email or mobile
    otp_hash = Column(String, nullable=False)
    purpose = Column(String, default="REGISTRATION", nullable=False) # REGISTRATION, PASSWORD_RESET, CONTACT_UPDATE
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
