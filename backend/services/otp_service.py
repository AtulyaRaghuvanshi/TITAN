import os
import random
import time
from typing import Optional, Dict

try:
    # Lazy import – optional dependency
    from sendgrid import SendGridAPIClient  # type: ignore
    from sendgrid.helpers.mail import Mail  # type: ignore
except Exception:  # pragma: no cover
    SendGridAPIClient = None  # type: ignore
    Mail = None  # type: ignore


class OTPService:
    """
    Simple in-memory OTP service for demo purposes.
    - Generates a 6-digit OTP per email
    - Stores with expiry (default 5 minutes)
    - Optionally exposes OTP in response for local demos if DEMO_EXPOSE_OTP=true
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: Dict[str, Dict[str, float]] = {}
        self._expose_demo = os.getenv("DEMO_EXPOSE_OTP", "false").lower() in ("1", "true", "yes")
        # Email config
        self.sg_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL") or os.getenv("SENDGRID_FROM_EMAIL")
        self.from_name = os.getenv("FROM_NAME") or "Titan Virtual Assistant"

    def _now(self) -> float:
        return time.time()

    def generate_otp(self, email: str) -> Dict[str, str]:
        code = f"{random.randint(0, 999999):06d}"
        self._store[email.lower()] = {"code": code, "expires": self._now() + self.ttl}
        # Attempt to send via SendGrid if configured
        sent = False
        if self.sg_api_key and self.from_email and SendGridAPIClient and Mail:
            try:
                subject = "Your Titan verification code"
                body = (
                    f"Hello,\n\n"
                    f"Your one-time password (OTP) is: {code}\n\n"
                    f"This code will expire in {int(self.ttl/60)} minutes.\n\n"
                    f"If you did not request this, you can ignore this email.\n\n"
                    f"Warm regards,\n"
                    f"{self.from_name}"
                )
                message = Mail(
                    from_email=(self.from_email, self.from_name),
                    to_emails=email,
                    subject=subject,
                    plain_text_content=body,
                )
                sg = SendGridAPIClient(self.sg_api_key)
                sg.send(message)
                sent = True
            except Exception:
                # Fail open – still allow OTP via demo hint if enabled
                sent = False

        resp = {"status": "sent" if sent else "queued"}
        if self._expose_demo:
            resp["otp"] = code
        return resp

    def verify_otp(self, email: str, code: str) -> bool:
        rec = self._store.get(email.lower())
        if not rec:
            return False
        if rec["expires"] < self._now():
            # expired
            del self._store[email.lower()]
            return False
        if str(rec["code"]) == str(code).zfill(6):
            # success, clear
            del self._store[email.lower()]
            return True
        return False

    def resend(self, email: str) -> Dict[str, str]:
        return self.generate_otp(email)
