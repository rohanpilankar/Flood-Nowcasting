from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.models.audit_log import AuditLog
from backend.app.schemas.auth import UserPublicSchema
from backend.app.schemas.government import (
    GovernmentInviteRequest,
    GovernmentVerifyRequest,
    GovernmentAuthorityItem
)
from backend.app.schemas.feedback import (
    CitizenFloodReportResponse,
    ReportReviewRequest,
    GroundTruthEvaluationSummary
)
from backend.app.services.auth_service import require_admin
from backend.app.services.government_service import GovernmentService
from backend.app.services.feedback_service import FeedbackService
from backend.app.services.model_evaluation_service import ModelEvaluationService

router = APIRouter(prefix="/admin", tags=["Administrator & Authority Management"])

class RoleUpdateRequest(BaseModel):
    role: str

class StatusUpdateRequest(BaseModel):
    status: str # ACTIVE, SUSPENDED, PENDING, VERIFIED

class AlertThresholdsUpdateRequest(BaseModel):
    alert_buffer_meters: Optional[float] = None
    alert_cooldown_minutes: Optional[int] = None
    location_max_age_hours: Optional[int] = None

@router.get("/users", response_model=List[UserPublicSchema])
def list_users(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserPublicSchema.from_orm(u) for u in users]

@router.patch("/users/{user_id}/role", response_model=UserPublicSchema)
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.role = payload.role
    log = AuditLog(
        actor_user_id=current_admin.id,
        action="UPDATE_USER_ROLE",
        target_type="USER",
        target_id=str(user.id),
        details=f"Role changed to {payload.role}"
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return UserPublicSchema.from_orm(user)

@router.patch("/users/{user_id}/status", response_model=UserPublicSchema)
def update_user_status(
    user_id: int,
    payload: StatusUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.status = payload.status
    log = AuditLog(
        actor_user_id=current_admin.id,
        action="UPDATE_USER_STATUS",
        target_type="USER",
        target_id=str(user.id),
        details=f"Status changed to {payload.status}"
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return UserPublicSchema.from_orm(user)

@router.post("/government/invite")
def invite_government_official(
    payload: GovernmentInviteRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return GovernmentService.invite_official(current_admin.id, payload, db)

@router.patch("/government/{user_id}/verify")
def verify_government_official(
    user_id: int,
    payload: GovernmentVerifyRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    profile = GovernmentService.verify_official(current_admin.id, user_id, payload, db)
    return {
        "success": True,
        "message": f"Government profile verification status set to {profile.verification_status}",
        "user_id": user_id,
        "verification_status": profile.verification_status
    }

@router.get("/government/authorities", response_model=List[GovernmentAuthorityItem])
def list_government_authorities(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return GovernmentService.list_authorities(db)

@router.get("/feedback", response_model=List[CitizenFloodReportResponse])
def get_all_feedback_reports(
    status_filter: Optional[str] = Query(None, description="UNVERIFIED, VALIDATED, REJECTED"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    reports = FeedbackService.get_all_reports(db, status_filter)
    results = []
    for r in reports:
        results.append(CitizenFloodReportResponse(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user.full_name if r.user else "Citizen",
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
        ))
    return results

@router.patch("/feedback/{report_id}/review", response_model=CitizenFloodReportResponse)
def review_feedback_report(
    report_id: int,
    payload: ReportReviewRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    report = FeedbackService.review_report(current_admin.id, report_id, payload, db)
    return CitizenFloodReportResponse(
        id=report.id,
        user_id=report.user_id,
        user_name=report.user.full_name if report.user else "Citizen",
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

@router.get("/model-evaluation", response_model=GroundTruthEvaluationSummary)
def get_model_evaluation(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    summary = ModelEvaluationService.get_ground_truth_summary(db)
    return GroundTruthEvaluationSummary(**summary)

@router.patch("/alert-thresholds")
def update_alert_thresholds(
    payload: AlertThresholdsUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if payload.alert_buffer_meters is not None:
        settings.ALERT_ZONE_BUFFER_METERS = payload.alert_buffer_meters
    if payload.alert_cooldown_minutes is not None:
        settings.ALERT_COOLDOWN_MINUTES = payload.alert_cooldown_minutes
    if payload.location_max_age_hours is not None:
        settings.LOCATION_MAX_AGE_HOURS = payload.location_max_age_hours

    log = AuditLog(
        actor_user_id=current_admin.id,
        action="UPDATE_ALERT_THRESHOLDS",
        target_type="CONFIG",
        target_id="SETTINGS",
        details=f"Buffer: {settings.ALERT_ZONE_BUFFER_METERS}m, Cooldown: {settings.ALERT_COOLDOWN_MINUTES}m"
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "message": "Alert thresholds and buffer settings updated successfully.",
        "alert_buffer_meters": settings.ALERT_ZONE_BUFFER_METERS,
        "alert_cooldown_minutes": settings.ALERT_COOLDOWN_MINUTES,
        "location_max_age_hours": settings.LOCATION_MAX_AGE_HOURS
    }
