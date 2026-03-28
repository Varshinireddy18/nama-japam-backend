import random
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

OTP_API_KEY = os.getenv("OTP_API_KEY")


def generate_otp() -> str:
    """Generates a cryptographically secure 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)


def send_otp(phone: str, otp: str) -> bool:
    """
    Send an OTP via SMS.

    TODO: Replace the print() below with a real SMS provider call.
    Example providers:
      - Twilio:    https://www.twilio.com/docs/sms
      - Fast2SMS:  https://www.fast2sms.com/
      - MSG91:     https://msg91.com/

    The API key is loaded from OTP_API_KEY in .env
    """
    if not OTP_API_KEY or OTP_API_KEY == "your_otp_api_key_here":
        # Development fallback — print OTP to console
        print(f"[DEV] OTP for {phone}: {otp}  (no SMS provider configured)")
        return True

    # --- Replace below with your real provider call ---
    # import requests
    # requests.post("https://your-provider/send", json={
    #     "apikey": OTP_API_KEY, "phone": phone, "message": f"Your OTP is {otp}"
    # })
    print(f"[PROD] Would send OTP {otp} to {phone} via SMS provider")
    return True
