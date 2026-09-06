import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash
from backend.app.db.models.user import User
from backend.app.db.models.government_profile import GovernmentProfile
from backend.app.db.models.audit_log import AuditLog
from backend.app.schemas.government import GovernmentInviteRequest, GovernmentVerifyRequest, GovernmentAuthorityItem

class GovernmentService:
    @staticmethod
    def invite_official(admin_id: int, payload: GovernmentInviteRequest, db: Session) -> dict:
        existing = db.query(User).filter(User.email == payload.email.lower()).first()
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists.")

        temp_password = "Gov@" + secrets.token_hex(4)
        invitation_token = secrets.token_urlsafe(24)

        user = User(
            full_name=payload.full_name.strip(),
            email=payload.email.lower().strip(),
            mobile=payload.official_phone.strip(),
            password_hash=get_password_hash(temp_password),
            role=payload.role,
            status="PENDING", # Requires admin verification
            email_verified=True,
            mobile_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = GovernmentProfile(
            user_id=user.id,
            organization_name=payload.organization_name.strip(),
            department=payload.department.strip(),
            designation=payload.designation.strip(),
            official_email=payload.email.lower().strip(),
            official_phone=payload.official_phone.strip(),
            jurisdiction=payload.jurisdiction.strip(),
            verification_status="PENDING",
            invitation_token=invitation_token
        )
        db.add(profile)

        # Audit Log
        log = AuditLog(
            actor_user_id=admin_id,
            action="INVITE_GOVERNMENT_OFFICIAL",
            target_type="USER",
            target_id=str(user.id),
            details=f"Invited {payload.full_name} ({payload.email}) as {payload.role}"
        )
        db.add(log)
        db.commit()

        print(f"[GOV SERVICE] Invited {payload.email}. Temp Password: {temp_password}, Token: {invitation_token}")

        return {
            "user_id": user.id,
            "email": user.email,
            "temporary_password": temp_password,
            "invitation_token": invitation_token,
            "status": "PENDING"
        }

    @staticmethod
    def verify_official(admin_id: int, user_id: int, payload: GovernmentVerifyRequest, db: Session) -> GovernmentProfile:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.government_profile:
            raise HTTPException(status_code=404, detail="Government official profile not found.")

        profile = user.government_profile
        profile.verification_status = payload.status
        user.status = payload.status

        if payload.status == "VERIFIED":
            profile.verified_by = admin_id
            profile.verified_at = datetime.now(timezone.utc)

        # Audit Log
        log = AuditLog(
            actor_user_id=admin_id,
            action=f"SET_STATUS_{payload.status}",
            target_type="GOVERNMENT_PROFILE",
            target_id=str(profile.id),
            details=payload.notes or f"Status set to {payload.status}"
        )
        db.add(log)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def list_authorities(db: Session) -> List[GovernmentAuthorityItem]:
        profiles = db.query(GovernmentProfile).all()
        results = []
        for p in profiles:
            u = p.user
            results.append(GovernmentAuthorityItem(
                user_id=u.id,
                full_name=u.full_name,
                email=u.email,
                role=u.role,
                status=u.status,
                organization_name=p.organization_name,
                department=p.department,
                designation=p.designation,
                official_phone=p.official_phone,
                jurisdiction=p.jurisdiction,
                verification_status=p.verification_status,
                verified_at=p.verified_at,
                created_at=p.created_at
            ))
        return results
