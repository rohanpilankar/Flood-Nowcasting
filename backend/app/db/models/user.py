from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="CITIZEN", nullable=False) # CITIZEN, GOVERNMENT_VIEWER, GOVERNMENT_OPERATOR, GOVERNMENT_SUPERVISOR, ADMIN
    status = Column(String, default="ACTIVE", nullable=False) # ACTIVE, PENDING, VERIFIED, SUSPENDED
    preferred_language = Column(String, default="en", nullable=False)

    email_verified = Column(Boolean, default=False, nullable=False)
    mobile_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    mobile_verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    government_profile = relationship("GovernmentProfile", foreign_keys="[GovernmentProfile.user_id]", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alert_preferences = relationship("CitizenAlertPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")
    saved_locations = relationship("SavedLocation", back_populates="user", cascade="all, delete-orphan")
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    alert_deliveries = relationship("AlertDelivery", back_populates="user", cascade="all, delete-orphan")
    flood_reports = relationship("CitizenFloodReport", foreign_keys="[CitizenFloodReport.user_id]", back_populates="user", cascade="all, delete-orphan")
