from datetime import datetime, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.models.citizen_preference import CitizenAlertPreferences
from backend.app.db.models.emergency_contact import EmergencyContact
from backend.app.schemas.auth import CitizenRegisterRequest

security_scheme = HTTPBearer(auto_error=True)

class AuthService:
    @staticmethod
    def register_citizen(payload: CitizenRegisterRequest, db: Session) -> User:
        if payload.password != payload.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")

        # Check duplicate email
        existing_email = db.query(User).filter(User.email == payload.email.lower()).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")

        # Check duplicate mobile
        existing_mobile = db.query(User).filter(User.mobile == payload.mobile).first()
        if existing_mobile:
            raise HTTPException(status_code=400, detail="An account with this mobile number already exists.")

        # Create Citizen User (Strictly CITIZEN role)
        user = User(
            full_name=payload.full_name.strip(),
            email=payload.email.lower().strip(),
            mobile=payload.mobile.strip(),
            password_hash=get_password_hash(payload.password),
            role="CITIZEN",
            status="ACTIVE",
            preferred_language=payload.preferred_language,
            email_verified=False,
            mobile_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create Preferences
        pref_data = payload.alert_preferences
        prefs = CitizenAlertPreferences(
            user_id=user.id,
            flood_alerts_enabled=pref_data.flood_alerts_enabled if pref_data else True,
            route_warnings_enabled=pref_data.route_warnings_enabled if pref_data else True,
            high_risk_alerts_enabled=pref_data.high_risk_alerts_enabled if pref_data else True,
            push_enabled=pref_data.push_enabled if pref_data else True,
            email_enabled=pref_data.email_enabled if pref_data else False,
            sms_enabled=pref_data.sms_enabled if pref_data else False,
            location_alerts_enabled=pref_data.location_alerts_enabled if pref_data else False,
            emergency_contact_notifications_enabled=pref_data.emergency_contact_notifications_enabled if pref_data else False
        )
        db.add(prefs)

        # Optional Emergency Contact
        if payload.emergency_contact and payload.emergency_contact.mobile:
            ec = EmergencyContact(
                user_id=user.id,
                full_name=payload.emergency_contact.full_name,
                relationship_type=payload.emergency_contact.relationship_type,
                mobile=payload.emergency_contact.mobile,
                verified=False,
                notification_consent=False
            )
            db.add(ec)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(login_id: str, password: str, db: Session) -> Optional[User]:
        clean_id = login_id.strip().lower()
        user = db.query(User).filter((User.email == clean_id) | (User.mobile == login_id.strip())).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.status == "SUSPENDED":
            raise HTTPException(status_code=403, detail="Account is suspended. Please contact administrator.")
        return user

    @staticmethod
    def create_tokens_for_user(user: User) -> dict:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    if user.status == "SUSPENDED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended.")

    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user

def require_verified_government(current_user: User = Depends(get_current_user)) -> User:
    gov_roles = ["GOVERNMENT_VIEWER", "GOVERNMENT_OPERATOR", "GOVERNMENT_SUPERVISOR"]
    if current_user.role not in gov_roles and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Government authority access required.")
    if current_user.role != "ADMIN" and current_user.status != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Government account pending administrator verification."
        )
    return current_user
