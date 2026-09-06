import random
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.db.models.otp import OtpVerification
from backend.app.db.models.user import User

class OtpService:
    @staticmethod
    def _hash_otp(code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    @classmethod
    def generate_and_send_otp(cls, target: str, purpose: str, db: Session, user_id: int = None) -> dict:
        # Invalidate any pending OTP for this target and purpose
        db.query(OtpVerification).filter(
            OtpVerification.target == target,
            OtpVerification.purpose == purpose,
            OtpVerification.verified_at == None
        ).delete()
        db.commit()

        # Generate 6-digit numeric OTP
        otp_code = str(random.randint(100000, 999999))
        otp_hash = cls._hash_otp(otp_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        otp_record = OtpVerification(
            user_id=user_id,
            target=target,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=expires_at,
            attempt_count=0
        )
        db.add(otp_record)
        db.commit()

        # In dev/mock mode, log OTP clearly
        print(f"[OTP SERVICE] Generated {purpose} OTP for {target}: {otp_code} (Valid for {settings.OTP_EXPIRE_MINUTES} mins)")

        return {
            "success": True,
            "message": f"Verification OTP sent to {target}. (Mock Code for Local Testing: {otp_code})",
            "target": target,
            "is_mock": True,
            "verified": False
        }

    @classmethod
    def verify_otp(cls, target: str, otp_code: str, purpose: str, db: Session) -> bool:
        now = datetime.now(timezone.utc)
        record = db.query(OtpVerification).filter(
            OtpVerification.target == target,
            OtpVerification.purpose == purpose,
            OtpVerification.verified_at == None,
            OtpVerification.expires_at > now
        ).first()

        if not record:
            return False

        if record.attempt_count >= settings.OTP_MAX_ATTEMPTS:
            return False

        record.attempt_count += 1
        db.commit()

        computed_hash = cls._hash_otp(otp_code)
        if computed_hash == record.otp_hash:
            record.verified_at = now
            # Update user if target matches
            user = db.query(User).filter((User.email == target) | (User.mobile == target)).first()
            if user:
                if "@" in target:
                    user.email_verified = True
                    user.email_verified_at = now
                else:
                    user.mobile_verified = True
                    user.mobile_verified_at = now
            db.commit()
            return True

        return False
