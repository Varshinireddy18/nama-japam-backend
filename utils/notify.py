import firebase_admin
from firebase_admin import credentials, messaging
import os

# Initialize Firebase — requires serviceAccountKey.json in production.
# If missing, notifications are silently skipped so the backend still starts.
_firebase_ready = False
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    _firebase_ready = True
except Exception as e:
    print(f"[WARNING] Firebase not initialized — push notifications disabled. Reason: {e}")

def send_fcm_notification(token: str, title: str, body: str, data: dict = None):
    if not _firebase_ready or not token:
        print(f"[WARNING] FCM skipped (Firebase not ready or no token).")
        return None

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=token,
    )

    try:
        response = messaging.send(message)
        return response
    except Exception as e:
        print(f"FCM Send Error: {e}")
        return None

def notify_group_members(tokens: list[str], title: str, body: str):
    if not _firebase_ready or not tokens:
        print(f"[WARNING] FCM batch skipped (Firebase not ready or no tokens).")
        return None

    messages = [
        messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token
        ) for token in tokens
    ]

    try:
        response = messaging.send_all(messages)
        return response
    except Exception as e:
        print(f"FCM Batch Error: {e}")
        return None
