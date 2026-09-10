from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.alert import FloodAlertSchema
from backend.app.services.alert_service import AlertService

router = APIRouter()

@router.get("/alerts", response_model=List[FloodAlertSchema])
def get_alerts(status: Optional[str] = Query(None, description="ACTIVE, ACKNOWLEDGED, RESOLVED")):
    service = AlertService.get_instance()
    return service.get_alerts(status=status)

@router.patch("/alerts/{alert_id}/acknowledge", response_model=FloodAlertSchema)
def acknowledge_alert(alert_id: str):
    service = AlertService.get_instance()
    alert = service.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert

@router.patch("/alerts/{alert_id}/resolve", response_model=FloodAlertSchema)
def resolve_alert(alert_id: str):
    service = AlertService.get_instance()
    alert = service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert
