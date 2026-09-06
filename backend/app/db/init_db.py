from datetime import datetime, timedelta, timezone
import json
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.db.models import (
    User,
    GovernmentProfile,
    CitizenAlertPreferences,
    UserLocation,
    SavedLocation,
    EmergencyContact,
    EmergencyAlert,
    AlertDelivery
)

def init_db(db: Session) -> None:
    # 1. Create all tables
    Base.metadata.create_all(bind=engine)

    # 2. Seed development accounts if enabled
    if not settings.ENABLE_DEMO_SEED:
        return

    # Check if admin already exists
    admin_user = db.query(User).filter(User.email == "admin@floodwatch.mumbai.gov.in").first()
    if not admin_user:
        admin_user = User(
            full_name="System Administrator (EOC Mumbai)",
            email="admin@floodwatch.mumbai.gov.in",
            mobile="+919820011111",
            password_hash=get_password_hash("Admin@Mumbai2026"),
            role="ADMIN",
            status="VERIFIED",
            email_verified=True,
            mobile_verified=True,
            email_verified_at=datetime.now(timezone.utc),
            mobile_verified_at=datetime.now(timezone.utc)
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    # Verified Government Official
    gov_user = db.query(User).filter(User.email == "eoc.officer@mcgm.gov.in").first()
    if not gov_user:
        gov_user = User(
            full_name="Rajesh Sharma (EOC Watch Officer)",
            email="eoc.officer@mcgm.gov.in",
            mobile="+919820022222",
            password_hash=get_password_hash("Gov@Mumbai2026"),
            role="GOVERNMENT_OPERATOR",
            status="VERIFIED",
            email_verified=True,
            mobile_verified=True,
            email_verified_at=datetime.now(timezone.utc),
            mobile_verified_at=datetime.now(timezone.utc)
        )
        db.add(gov_user)
        db.commit()
        db.refresh(gov_user)

        gov_profile = GovernmentProfile(
            user_id=gov_user.id,
            organization_name="Brihanmumbai Municipal Corporation (BMC)",
            department="Disaster Management Cell",
            designation="Senior EOC Operations Officer",
            official_email="eoc.officer@mcgm.gov.in",
            official_phone="+91-22-22694725",
            jurisdiction="BMC Wards F/North, F/South, G/North (Central Mumbai)",
            verification_status="VERIFIED",
            verified_by=admin_user.id,
            verified_at=datetime.now(timezone.utc)
        )
        db.add(gov_profile)
        db.commit()

    # Pending Government Official
    pending_gov = db.query(User).filter(User.email == "ward.trainee@mcgm.gov.in").first()
    if not pending_gov:
        pending_gov = User(
            full_name="Pooja Kulkarni (Ward H/East Analyst)",
            email="ward.trainee@mcgm.gov.in",
            mobile="+919820033333",
            password_hash=get_password_hash("Pending@2026"),
            role="GOVERNMENT_VIEWER",
            status="PENDING",
            email_verified=True,
            mobile_verified=False,
            email_verified_at=datetime.now(timezone.utc)
        )
        db.add(pending_gov)
        db.commit()
        db.refresh(pending_gov)

        pending_profile = GovernmentProfile(
            user_id=pending_gov.id,
            organization_name="BMC Ward H/East Office",
            department="Storm Water Drains Department",
            designation="Assistant Drainage Inspector",
            official_email="ward.trainee@mcgm.gov.in",
            official_phone="+91-22-26182222",
            jurisdiction="Ward H/East (Santacruz East)",
            verification_status="PENDING"
        )
        db.add(pending_profile)
        db.commit()

    # Opted-In Citizen (located near Hindmata Saucer Basin)
    citizen_user = db.query(User).filter(User.email == "rohan.citizen@gmail.com").first()
    if not citizen_user:
        citizen_user = User(
            full_name="Rohan Varma (Citizen)",
            email="rohan.citizen@gmail.com",
            mobile="+919820044444",
            password_hash=get_password_hash("Citizen@2026"),
            role="CITIZEN",
            status="ACTIVE",
            email_verified=True,
            mobile_verified=True,
            email_verified_at=datetime.now(timezone.utc),
            mobile_verified_at=datetime.now(timezone.utc)
        )
        db.add(citizen_user)
        db.commit()
        db.refresh(citizen_user)

        # Preferences
        prefs = CitizenAlertPreferences(
            user_id=citizen_user.id,
            flood_alerts_enabled=True,
            route_warnings_enabled=True,
            high_risk_alerts_enabled=True,
            push_enabled=True,
            email_enabled=True,
            sms_enabled=False, # marked as unconfigured
            location_alerts_enabled=True,
            emergency_contact_notifications_enabled=False
        )
        db.add(prefs)

        # Active Session Location in Hindmata Basin (19.0125, 72.8428)
        now = datetime.now(timezone.utc)
        loc = UserLocation(
            user_id=citizen_user.id,
            latitude=19.0125,
            longitude=72.8428,
            accuracy_meters=8.5,
            captured_at=now,
            consent_status=True,
            location_source="CURRENT_SESSION",
            expires_at=now + timedelta(hours=settings.LOCATION_MAX_AGE_HOURS)
        )
        db.add(loc)

        # Saved Location (Home in Dadar)
        home = SavedLocation(
            user_id=citizen_user.id,
            label="Home (Dadar East)",
            latitude=19.0178,
            longitude=72.8478,
            alerts_enabled=True
        )
        db.add(home)

        # Optional Emergency Contact
        ec = EmergencyContact(
            user_id=citizen_user.id,
            full_name="Sunita Varma",
            relationship_type="Family",
            mobile="+919820055555",
            verified=False,
            notification_consent=False
        )
        db.add(ec)
        db.commit()

    # Initial Emergency Alert over Hindmata & Milan Subways
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.alert_code == "ALT-MUM-2026-001").first()
    if not alert:
        now = datetime.now(timezone.utc)
        # Hindmata Polygon GeoJSON
        hindmata_poly = {
            "type": "Polygon",
            "coordinates": [[
                [72.835, 19.005],
                [72.850, 19.005],
                [72.850, 19.020],
                [72.835, 19.020],
                [72.835, 19.005]
            ]]
        }
        alert = EmergencyAlert(
            alert_code="ALT-MUM-2026-001",
            title="Severe Inundation Alert — Hindmata Saucer Basin",
            location_name="Hindmata Chowk, Dadar East (Ward F/South)",
            alert_type="FLOOD_INUNDATION",
            severity="CRITICAL",
            risk_score=92,
            model_confidence=95,
            forecast_horizon="+1H",
            geometry_geojson=json.dumps(hindmata_poly),
            description="Extreme depression basin water accumulation exceeding 55cm. Dr. Ambedkar Road low grade submerged. Traffic Police diversion active.",
            recommended_action="Avoid traveling through Hindmata. Use Hindmata Flyover or Western Express Highway elevated bypass.",
            model_version="XGBoost-v2.0-Mumbai",
            status="ACTIVE",
            prediction_timestamp=now,
            created_at=now,
            last_updated=now,
            expires_at=now + timedelta(hours=2)
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Deliver to citizen in Hindmata
        if citizen_user:
            delivery = AlertDelivery(
                alert_id=alert.id,
                user_id=citizen_user.id,
                channel="IN_APP",
                delivery_status="SENT",
                sent_at=now
            )
            db.add(delivery)
            db.commit()

    print("[OK] Database initialized and development seed accounts created.")
