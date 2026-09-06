from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String, unique=True, index=True, nullable=False) # e.g. ALT-MUM-2026-001
    title = Column(String, nullable=False)
    location_name = Column(String, nullable=False)
    alert_type = Column(String, default="FLOOD_INUNDATION", nullable=False)
    severity = Column(String, default="HIGH", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Integer, nullable=False) # 0 - 100
    model_confidence = Column(Integer, default=85, nullable=False) # 0 - 100
    forecast_horizon = Column(String, default="+1H", nullable=False) # NOW, +30M, +1H, +2H, +3H
    geometry_geojson = Column(Text, nullable=False) # Alert Polygon GeoJSON string
    description = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    model_version = Column(String, default="XGBoost-v2.0-Mumbai", nullable=False)
    status = Column(String, default="ACTIVE", nullable=False) # ACTIVE, ACKNOWLEDGED, EXPIRED, RESOLVED

    prediction_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    deliveries = relationship("AlertDelivery", back_populates="alert", cascade="all, delete-orphan")
    reports = relationship("CitizenFloodReport", back_populates="alert")
