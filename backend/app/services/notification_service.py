from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session

class NotificationProvider(ABC):
    @abstractmethod
    def send(self, recipient: str, title: str, body: str, metadata: Dict[str, Any]) -> bool:
        pass

class InAppNotificationProvider(NotificationProvider):
    def send(self, recipient: str, title: str, body: str, metadata: Dict[str, Any]) -> bool:
        # In-app notifications are stored directly in AlertDelivery
        return True

class WebPushNotificationProvider(NotificationProvider):
    def send(self, recipient: str, title: str, body: str, metadata: Dict[str, Any]) -> bool:
        # Prototype notice: WebPush requires VAPID keys
        print(f"[PUSH STUB] WebPush provider unconfigured. Notification queued: {title}")
        return False

class EmailNotificationProvider(NotificationProvider):
    def send(self, recipient: str, title: str, body: str, metadata: Dict[str, Any]) -> bool:
        # Prototype notice: SMTP server unconfigured
        print(f"[EMAIL STUB] Email provider unconfigured. Recipient: {recipient}")
        return False

class SmsNotificationProvider(NotificationProvider):
    def send(self, recipient: str, title: str, body: str, metadata: Dict[str, Any]) -> bool:
        # Prototype notice: SMS gateway unconfigured
        print(f"[SMS STUB] SMS provider unconfigured. Recipient: {recipient}")
        return False

class NotificationService:
    in_app = InAppNotificationProvider()
    web_push = WebPushNotificationProvider()
    email = EmailNotificationProvider()
    sms = SmsNotificationProvider()

    @classmethod
    def dispatch(cls, channel: str, recipient: str, title: str, body: str, metadata: Dict[str, Any] = None) -> bool:
        ch = channel.upper()
        if ch == "IN_APP":
            return cls.in_app.send(recipient, title, body, metadata or {})
        elif ch == "PUSH":
            return cls.web_push.send(recipient, title, body, metadata or {})
        elif ch == "EMAIL":
            return cls.email.send(recipient, title, body, metadata or {})
        elif ch == "SMS":
            return cls.sms.send(recipient, title, body, metadata or {})
        return False
