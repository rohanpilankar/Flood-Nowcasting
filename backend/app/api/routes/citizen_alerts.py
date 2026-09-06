from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.schemas.alert_targeting import CitizenAlertItem
from backend.app.services.auth_service import get_current_user
from backend.app.services.alert_targeting_service import AlertTargetingService

router = APIRouter(prefix="/alerts", tags=["Targeted Citizen Alerts"])

@router.get("/my-alerts", response_model=List[CitizenAlertItem])
def get_my_targeted_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Trigger spatial check and delivery sync
    AlertTargetingService.sync_ml_alerts_and_target(db)
    # Fetch user's deliveries
    alerts = AlertTargetingService.get_citizen_alerts(current_user.id, db)
    return alerts

@router.patch("/{delivery_id}/read")
def mark_alert_read(
    delivery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = AlertTargetingService.mark_alert_read(delivery_id, current_user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Alert delivery record not found.")
    return {"success": True, "message": "Alert marked as read."}
