from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.alert import FloodAlertSchema
from backend.app.services.flood_service import FloodService

router = APIRouter()

@router.get("/alerts", response_model=List[FloodAlertSchema])
def get_alerts():
    service = FloodService.get_instance()
    return service.get_alerts()

@router.patch("/alerts/{alert_id}/acknowledge", response_model=FloodAlertSchema)
def acknowledge_alert(alert_id: str):
    service = FloodService.get_instance()
    alert = service.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert
