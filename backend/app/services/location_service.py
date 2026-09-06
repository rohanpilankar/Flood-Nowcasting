from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.models.user_location import UserLocation
from backend.app.db.models.saved_location import SavedLocation
from backend.app.db.models.citizen_preference import CitizenAlertPreferences
from backend.app.schemas.location import LocationUpdateRequest, SavedLocationCreate

class LocationService:
    @staticmethod
    def update_user_location(user_id: int, payload: LocationUpdateRequest, db: Session) -> UserLocation:
        if not payload.consent_status:
            raise HTTPException(
                status_code=400,
                detail="Explicit location consent is required to store coordinates."
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=settings.LOCATION_MAX_AGE_HOURS)

        # Deactivate old current session records
        db.query(UserLocation).filter(
            UserLocation.user_id == user_id,
            UserLocation.location_source == "CURRENT_SESSION"
        ).delete()

        new_location = UserLocation(
            user_id=user_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_meters=payload.accuracy_meters,
            captured_at=now,
            consent_status=True,
            location_source=payload.location_source,
            expires_at=expires_at
        )
        db.add(new_location)

        # Ensure user's preferences show location alerts enabled
        prefs = db.query(CitizenAlertPreferences).filter(CitizenAlertPreferences.user_id == user_id).first()
        if prefs:
            prefs.location_alerts_enabled = True

        db.commit()
        db.refresh(new_location)
        return new_location

    @staticmethod
    def get_active_user_location(user_id: int, db: Session) -> Optional[UserLocation]:
        now = datetime.now(timezone.utc)
        return db.query(UserLocation).filter(
            UserLocation.user_id == user_id,
            UserLocation.consent_status == True,
            UserLocation.expires_at > now
        ).order_by(UserLocation.captured_at.desc()).first()

    @staticmethod
    def delete_current_location(user_id: int, db: Session) -> None:
        db.query(UserLocation).filter(
            UserLocation.user_id == user_id,
            UserLocation.location_source == "CURRENT_SESSION"
        ).delete()

        # Set preference to disabled
        prefs = db.query(CitizenAlertPreferences).filter(CitizenAlertPreferences.user_id == user_id).first()
        if prefs:
            prefs.location_alerts_enabled = False

        db.commit()

    @staticmethod
    def delete_all_location_history(user_id: int, db: Session) -> int:
        count = db.query(UserLocation).filter(UserLocation.user_id == user_id).delete()
        prefs = db.query(CitizenAlertPreferences).filter(CitizenAlertPreferences.user_id == user_id).first()
        if prefs:
            prefs.location_alerts_enabled = False
        db.commit()
        return count

    @staticmethod
    def save_location(user_id: int, payload: SavedLocationCreate, db: Session) -> SavedLocation:
        saved = SavedLocation(
            user_id=user_id,
            label=payload.label.strip(),
            latitude=payload.latitude,
            longitude=payload.longitude,
            alerts_enabled=payload.alerts_enabled
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
        return saved

    @staticmethod
    def get_saved_locations(user_id: int, db: Session) -> List[SavedLocation]:
        return db.query(SavedLocation).filter(SavedLocation.user_id == user_id).all()

    @staticmethod
    def delete_saved_location(user_id: int, location_id: int, db: Session) -> bool:
        rec = db.query(SavedLocation).filter(
            SavedLocation.id == location_id,
            SavedLocation.user_id == user_id
        ).first()
        if rec:
            db.delete(rec)
            db.commit()
            return True
        return False
