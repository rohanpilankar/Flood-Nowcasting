from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.schemas.feedback import CitizenFloodReportCreate, CitizenFloodReportResponse
from backend.app.services.auth_service import get_current_user
from backend.app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Citizen Flood Feedback & Ground Truth"])

@router.post("/flood-report", response_model=CitizenFloodReportResponse)
def submit_flood_report(
    payload: CitizenFloodReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = FeedbackService.submit_report(current_user.id, payload, db)
    return CitizenFloodReportResponse(
        id=report.id,
        user_id=report.user_id,
        user_name=current_user.full_name,
        latitude=report.latitude,
        longitude=report.longitude,
        location_name=report.location_name,
        observation_status=report.observation_status,
        water_level=report.water_level,
        description=report.description,
        linked_grid_id=report.linked_grid_id,
        linked_alert_id=report.linked_alert_id,
        validation_status=report.validation_status,
        admin_notes=report.admin_notes,
        reported_at=report.reported_at,
        reviewed_at=report.reviewed_at
    )

@router.get("/my-reports", response_model=List[CitizenFloodReportResponse])
def get_my_flood_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = FeedbackService.get_citizen_reports(current_user.id, db)
    return [
        CitizenFloodReportResponse(
            id=r.id,
            user_id=r.user_id,
            user_name=current_user.full_name,
            latitude=r.latitude,
            longitude=r.longitude,
            location_name=r.location_name,
            observation_status=r.observation_status,
            water_level=r.water_level,
            description=r.description,
            linked_grid_id=r.linked_grid_id,
            linked_alert_id=r.linked_alert_id,
            validation_status=r.validation_status,
            admin_notes=r.admin_notes,
            reported_at=r.reported_at,
            reviewed_at=r.reviewed_at
        )
        for r in reports
    ]
