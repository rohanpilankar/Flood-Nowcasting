from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.schemas.location import (
    LocationUpdateRequest,
    LocationResponse,
    SavedLocationCreate,
    SavedLocationResponse
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.location_service import LocationService

router = APIRouter(prefix="/location", tags=["Consent-Based Location Services"])

@router.post("/update", response_model=LocationResponse)
def update_location(
    payload: LocationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loc = LocationService.update_user_location(current_user.id, payload, db)
    return LocationResponse(
        latitude=loc.latitude,
        longitude=loc.longitude,
        accuracy_meters=loc.accuracy_meters,
        captured_at=loc.captured_at,
        expires_at=loc.expires_at,
        consent_status=loc.consent_status,
        location_source=loc.location_source
    )

@router.get("/current", response_model=LocationResponse)
def get_current_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    loc = LocationService.get_active_user_location(current_user.id, db)
    if not loc:
        raise HTTPException(
            status_code=404,
            detail="No active location shared or location consent expired."
        )
    return LocationResponse(
        latitude=loc.latitude,
        longitude=loc.longitude,
        accuracy_meters=loc.accuracy_meters,
        captured_at=loc.captured_at,
        expires_at=loc.expires_at,
        consent_status=loc.consent_status,
        location_source=loc.location_source
    )

@router.delete("/current")
def delete_current_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    LocationService.delete_current_location(current_user.id, db)
    return {
        "success": True,
        "message": "Current session location removed and location alerts disabled."
    }

@router.delete("/history")
def delete_location_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deleted_count = LocationService.delete_all_location_history(current_user.id, db)
    return {
        "success": True,
        "message": f"Deleted {deleted_count} location history records and revoked active location sharing."
    }

@router.get("/saved", response_model=List[SavedLocationResponse])
def get_saved_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = LocationService.get_saved_locations(current_user.id, db)
    return [SavedLocationResponse.from_orm(s) for s in saved]

@router.post("/saved", response_model=SavedLocationResponse)
def create_saved_location(
    payload: SavedLocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = LocationService.save_location(current_user.id, payload, db)
    return SavedLocationResponse.from_orm(saved)

@router.delete("/saved/{location_id}")
def delete_saved_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = LocationService.delete_saved_location(current_user.id, location_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Saved location not found.")
    return {"success": True, "message": "Saved location deleted."}
