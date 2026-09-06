from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("emergency_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String, default="IN_APP", nullable=False) # IN_APP, PUSH, EMAIL, SMS
    delivery_status = Column(String, default="SENT", nullable=False) # SENT, READ, FAILED
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    alert = relationship("EmergencyAlert", back_populates="deliveries")
    user = relationship("User", back_populates="alert_deliveries")
