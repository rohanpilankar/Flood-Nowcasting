from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class CitizenAlertPreferences(Base):
    __tablename__ = "citizen_alert_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    flood_alerts_enabled = Column(Boolean, default=True, nullable=False)
    route_warnings_enabled = Column(Boolean, default=True, nullable=False)
    high_risk_alerts_enabled = Column(Boolean, default=True, nullable=False)

    push_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=False, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    location_alerts_enabled = Column(Boolean, default=False, nullable=False)
    emergency_contact_notifications_enabled = Column(Boolean, default=False, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="alert_preferences")
