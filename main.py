from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chant, groups, leaderboard, admin
from database import engine, Base
import os

# Create tables (For demo purposes; in production, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nama Japam Chanting App API")

# CORS — allow all origins in development.
# In production, set CORS_ORIGINS env var to restrict, e.g.:
#   CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
_raw_origins = os.getenv("CORS_ORIGINS", "")
if _raw_origins:
    _allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
    _allow_credentials = True
else:
    # Dev mode: allow all origins (wildcard). credentials must be False with "*".
    _allowed_origins = ["*"]
    _allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from utils.notify import send_fcm_notification
from database import SessionLocal
from models import User
import datetime

scheduler = BackgroundScheduler()

def morning_reminder():
    db = SessionLocal()
    users = db.query(User).filter(User.fcm_token.isnot(None)).all()
    for user in users:
        send_fcm_notification(user.fcm_token, "Morning Blessing 🙏", "Chant your Nama Japam today and stay connected.")
    db.close()

def evening_summary():
    db = SessionLocal()
    # Simplified logic: just a reminder. Real logic would calculate today's count.
    users = db.query(User).filter(User.fcm_token.isnot(None)).all()
    for user in users:
        send_fcm_notification(user.fcm_token, "Evening Reflection ✨", "You've made great progress today. Keep the name in your heart.")
    db.close()

scheduler.add_job(morning_reminder, 'cron', hour=8, minute=0)
scheduler.add_job(evening_summary, 'cron', hour=20, minute=0)
scheduler.start()

# Include Routers
app.include_router(auth.router)
app.include_router(chant.router)
app.include_router(groups.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Nama Japam Chanting App API"}
