from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database
from .auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_group = models.Group(**group.dict(), created_by=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # Auto-join the creator
    membership = models.UserGroup(user_id=current_user.id, group_id=db_group.id)
    db.add(membership)
    db.commit()

    return db_group

@router.get("/", response_model=List[schemas.Group])
def get_groups(db: Session = Depends(database.get_db)):
    return db.query(models.Group).filter(models.Group.is_active == True).all()

@router.post("/{group_id}/join")
def join_group(group_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Check if already a member
    existing = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == current_user.id,
        models.UserGroup.group_id == group_id
    ).first()
    if existing:
        return {"message": "Already a member"}

    membership = models.UserGroup(user_id=current_user.id, group_id=group_id)
    db.add(membership)
    db.commit()
    return {"message": "Joined group successfully"}
