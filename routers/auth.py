from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models
import schemas
import database
from utils import otp
from utils import jwt
from jose import JWTError, jwt as jose_jwt
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = jwt.verify_token(token)
    if payload is None:
        raise credentials_exception
    phone: str = payload.get("sub")
    if phone is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(token: str = Depends(oauth2_scheme)):
    """Verifies that the token has an admin role."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = jwt.verify_token(token)
    if payload is None:
        raise credentials_exception
    
    role = payload.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return payload.get("sub") # Returns "admin:username"

@router.post("/send-otp")
def send_otp_endpoint(data: schemas.OTPSend, db: Session = Depends(database.get_db)):
    gen_otp = otp.generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Save to DB
    otp_log = models.OTPLog(phone=data.phone, otp=gen_otp, expires_at=expires_at)
    db.add(otp_log)
    db.commit()
    
    # Mock send
    otp.send_otp(data.phone, gen_otp)
    
    return {"message": "OTP sent"}

@router.post("/verify-otp", response_model=schemas.Token)
def verify_otp(data: schemas.OTPVerify, db: Session = Depends(database.get_db)):
    # Validate OTP and expiry
    otp_record = db.query(models.OTPLog).filter(
        models.OTPLog.phone == data.phone,
        models.OTPLog.otp == data.otp,
        models.OTPLog.is_used == False,
        models.OTPLog.expires_at > datetime.utcnow()
    ).order_by(models.OTPLog.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    if otp_record:
        otp_record.is_used = True
        db.commit()
    
    user = db.query(models.User).filter(models.User.phone == data.phone).first()
    is_new_user = False
    if not user:
        # Create user with placeholder name
        user = models.User(phone=data.phone, name=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    elif user.name is None or user.name == "New User":
        is_new_user = True
    
    # Update FCM token if provided
    if data.fcm_token:
        user.fcm_token = data.fcm_token
        db.commit()

    access_token = jwt.create_access_token(data={"sub": user.phone})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "is_new_user": is_new_user,
        "user": user
    }

@router.post("/register", response_model=schemas.Token)
def register_user(data: schemas.UserSignup, db: Session = Depends(database.get_db)):
    # Check if user exists
    user = db.query(models.User).filter(models.User.phone == data.phone).first()
    if user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Create new user
    new_user = models.User(
        name=data.name,
        phone=data.phone,
        password=hash_password(data.password),
        fcm_token=data.fcm_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = jwt.create_access_token(data={"sub": new_user.phone})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_new_user": True,
        "user": new_user
    }

@router.post("/login", response_model=schemas.Token)
def login_user(data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.phone == data.phone).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    if user.password != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    # Update FCM token if provided
    if data.fcm_token:
        user.fcm_token = data.fcm_token
        db.commit()
        db.refresh(user)
    
    access_token = jwt.create_access_token(data={"sub": user.phone})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_new_user": False,
        "user": user
    }

@router.post("/update-name", response_model=schemas.User)
def update_name(data: schemas.UserRegister, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    current_user.name = data.name
    db.commit()
    db.refresh(current_user)
    return current_user
