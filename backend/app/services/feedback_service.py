from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.db.models.citizen_flood_report import CitizenFloodReport
from backend.app.db.models.audit_log import AuditLog
from backend.app.schemas.feedback import CitizenFloodReportCreate, ReportReviewRequest

class FeedbackService:
    @staticmethod
    def submit_report(user_id: int, payload: CitizenFloodReportCreate, db: Session) -> CitizenFloodReport:
        # Check spam/duplicate from same user within last 5 minutes at same coordinates
        recent_report = db.query(CitizenFloodReport).filter(
            CitizenFloodReport.user_id == user_id,
            CitizenFloodReport.observation_status == payload.observation_status
        ).order_by(CitizenFloodReport.reported_at.desc()).first()

        now = datetime.now(timezone.utc)
        if recent_report and recent_report.reported_at:
            rep_time = recent_report.reported_at
            if rep_time.tzinfo is None:
                rep_time = rep_time.replace(tzinfo=timezone.utc)
            if (now - rep_time).total_seconds() < 3:
                raise HTTPException(status_code=429, detail="Report already recorded. Please wait before submitting another update.")

        report = CitizenFloodReport(
            user_id=user_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_name=payload.location_name.strip(),
            observation_status=payload.observation_status,
            water_level=payload.water_level,
            description=payload.description.strip() if payload.description else None,
            photo_reference=payload.photo_reference,
            linked_grid_id=payload.linked_grid_id,
            linked_alert_id=payload.linked_alert_id,
            validation_status="UNVERIFIED",
            reported_at=now
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        print(f"[FEEDBACK] Citizen report #{report.id} received for {report.location_name} (Observation: {report.observation_status})")
        return report

    @staticmethod
    def review_report(admin_id: int, report_id: int, payload: ReportReviewRequest, db: Session) -> CitizenFloodReport:
        report = db.query(CitizenFloodReport).filter(CitizenFloodReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Citizen flood report not found.")

        now = datetime.now(timezone.utc)
        report.validation_status = payload.validation_status
        report.admin_notes = payload.admin_notes
        report.reviewed_by = admin_id
        report.reviewed_at = now

        # Audit Log
        log = AuditLog(
            actor_user_id=admin_id,
            action=f"REVIEW_REPORT_{payload.validation_status}",
            target_type="CITIZEN_FLOOD_REPORT",
            target_id=str(report.id),
            details=payload.admin_notes or f"Validation set to {payload.validation_status}"
        )
        db.add(log)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_citizen_reports(user_id: int, db: Session) -> List[CitizenFloodReport]:
        return db.query(CitizenFloodReport).filter(
            CitizenFloodReport.user_id == user_id
        ).order_by(CitizenFloodReport.reported_at.desc()).all()

    @staticmethod
    def get_all_reports(db: Session, status_filter: Optional[str] = None) -> List[CitizenFloodReport]:
        query = db.query(CitizenFloodReport)
        if status_filter:
            query = query.filter(CitizenFloodReport.validation_status == status_filter.upper())
        return query.order_by(CitizenFloodReport.reported_at.desc()).all()
