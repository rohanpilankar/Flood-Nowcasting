from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, nullable=True, index=True)
    action = Column(String, nullable=False) # e.g. VERIFY_GOVERNMENT_ACCOUNT, UPDATE_ALERT_THRESHOLDS, VALIDATE_REPORT
    target_type = Column(String, nullable=False) # e.g. USER, ALERT, REPORT, SYSTEM
    target_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
