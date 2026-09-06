from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class CitizenFloodReport(Base):
    __tablename__ = "citizen_flood_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String, default="Reported Location", nullable=False)
    observation_status = Column(String, default="YES", nullable=False) # YES, NO, NOT_SURE
    water_level = Column(String, default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, NONE
    description = Column(Text, nullable=True)
    photo_reference = Column(String, nullable=True)
    linked_grid_id = Column(String, nullable=True) # e.g. MUM_000102
    linked_alert_id = Column(Integer, ForeignKey("emergency_alerts.id", ondelete="SET NULL"), nullable=True)

    validation_status = Column(String, default="UNVERIFIED", nullable=False) # UNVERIFIED, REVIEWED, VALIDATED, REJECTED
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    admin_notes = Column(Text, nullable=True)
    reported_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="flood_reports")
    alert = relationship("EmergencyAlert", back_populates="reports")
