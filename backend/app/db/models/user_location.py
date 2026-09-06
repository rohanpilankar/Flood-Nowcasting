from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class UserLocation(Base):
    __tablename__ = "user_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Float, default=10.0, nullable=False)
    captured_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    consent_status = Column(Boolean, default=True, nullable=False)
    location_source = Column(String, default="CURRENT_SESSION", nullable=False) # CURRENT_SESSION, LAST_KNOWN, SAVED_LOCATION
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="locations")
