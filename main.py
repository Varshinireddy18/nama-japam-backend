from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chant, groups, leaderboard, admin
from database import engine, Base
import os

# ✅ Firebase imports
import firebase_admin
from firebase_admin import credentials

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nama Japam Chanting App API")

# ------------------- CORS -------------------
_raw_origins = os.getenv("CORS_ORIGINS", "")
if _raw_origins:
    _allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
    _allow_credentials = True
else:
    _allowed_origins = ["*"]
    _allow_credentials = False
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nama-japam-chanting-app.netlify.app",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
# ------------------- ✅ Firebase Setup -------------------
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": "nama-japam-chanting-app",
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token"
    })
    firebase_admin.initialize_app(cred)

# ------------------- Scheduler -------------------
from apscheduler.schedulers.background import BackgroundScheduler
from utils.notify import send_fcm_notification
from database import SessionLocal
from models import User

scheduler = BackgroundScheduler()

def morning_reminder():
    db = SessionLocal()
    users = db.query(User).filter(User.fcm_token.isnot(None)).all()
    for user in users:
        send_fcm_notification(
            user.fcm_token,
            "Morning Blessing 🙏",
            "Chant your Nama Japam today and stay connected."
        )
    db.close()

def evening_summary():
    db = SessionLocal()
    users = db.query(User).filter(User.fcm_token.isnot(None)).all()
    for user in users:
        send_fcm_notification(
            user.fcm_token,
            "Evening Reflection ✨",
            "You've made great progress today. Keep the name in your heart."
        )
    db.close()

scheduler.add_job(morning_reminder, 'cron', hour=8, minute=0)
scheduler.add_job(evening_summary, 'cron', hour=20, minute=0)
scheduler.start()

# ------------------- Routers -------------------
app.include_router(auth.router)
app.include_router(chant.router)
app.include_router(groups.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)

# ------------------- Root -------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to Nama Japam Chanting App API "}