from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import models, database, schemas
from .auth import get_current_admin
from utils.jwt import create_access_token

router = APIRouter(prefix="/admin", tags=["admin"])

# ── Admin Login ──────────────────────────────────────────────────────────────
class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def admin_login(data: AdminLoginRequest):
    """Validate admin credentials from .env and return a bearer token."""
    valid_username = os.getenv("ADMIN_USERNAME", "admin")
    valid_password = os.getenv("ADMIN_PASSWORD", "admin123")

    if data.username != valid_username or data.password != valid_password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    token = create_access_token(data={"sub": f"admin:{data.username}", "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}



@router.get("/groups")
def list_groups(
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    return db.query(models.Group).all()

@router.post("/groups")
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    # Use a dummy admin ID for created_by or handle it appropriately
    db_group = models.Group(**group.dict(), created_by=admin_sub)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.put("/groups/{group_id}")
def update_group(
    group_id: str,
    group: schemas.GroupCreate,
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    for key, value in group.dict().items():
        setattr(db_group, key, value)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.delete("/groups/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    db_group.is_active = False
    db.commit()
    return {"message": "Group deactivated"}

@router.get("/users")
def list_users(
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    return db.query(models.User).all()

@router.post("/notify")
def send_group_notification(
    group_id: str,
    title: str,
    body: str,
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    from utils.notify import notify_group_members

    tokens = db.query(models.User.fcm_token).join(models.UserGroup).filter(
        models.UserGroup.group_id == group_id,
        models.User.fcm_token.isnot(None),
    ).all()

    token_list = [t[0] for t in tokens]
    if token_list:
        notify_group_members(token_list, title, body)

    return {"message": f"Notification sent to {len(token_list)} members"}

@router.post("/user/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    db: Session = Depends(database.get_db),
    admin_sub: str = Depends(get_current_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": "User deactivated"}
