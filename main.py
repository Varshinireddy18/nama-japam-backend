from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chant, groups, leaderboard, admin
from database import engine, Base
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nama Japam Chanting App API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nama-japam-chanting-app.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Firebase Setup - only if credentials are available
try:
    import firebase_admin
    from firebase_admin import credentials

    if not firebase_admin._apps:
        firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
        firebase_client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")

        if firebase_private_key and firebase_client_email:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": "nama-japam-chanting-app",
                "private_key": firebase_private_key.replace("\\n", "\n"),
                "client_email": firebase_client_email,
                "token_uri": "https://oauth2.googleapis.com/token"
            })
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully!")
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("Firebase initialized with serviceAccountKey.json!")
        else:
            print("Firebase: No credentials found - notifications disabled")
except Exception as e:
    print(f"Firebase Init Error: {e}")

# Scheduler - only if firebase is working
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from utils.notify import send_fcm_notification
    from database import SessionLocal
    from models import User

    scheduler = BackgroundScheduler()

    def morning_reminder():
        try:
            db = SessionLocal()
            users = db.query(User).filter(
                User.fcm_token.isnot(None)).all()
            for user in users:
                send_fcm_notification(
                    user.fcm_token,
                    "Morning Blessing 🙏",
                    "Chant your Nama Japam today and stay connected."
                )
            db.close()
        except Exception as e:
            print(f"Morning reminder error: {e}")

    def evening_summary():
        try:
            db = SessionLocal()
            users = db.query(User).filter(
                User.fcm_token.isnot(None)).all()
            for user in users:
                send_fcm_notification(
                    user.fcm_token,
                    "Evening Reflection ✨",
                    "You have made great progress today. Keep chanting!"
                )
            db.close()
        except Exception as e:
            print(f"Evening summary error: {e}")

    scheduler.add_job(morning_reminder, 'cron', hour=8, minute=0)
    scheduler.add_job(evening_summary, 'cron', hour=20, minute=0)
    scheduler.start()
    print("Scheduler started!")
except Exception as e:
    print(f"Scheduler Error: {e}")

# Routers
app.include_router(auth.router)
app.include_router(chant.router)
app.include_router(groups.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Nama Japam Chanting App API 🙏",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return {"message": "OK"}