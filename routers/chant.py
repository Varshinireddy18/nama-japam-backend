from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List
import models, schemas, database
from .auth import get_current_user

router = APIRouter(prefix="/chant", tags=["chant"])

@router.post("/add", response_model=schemas.ChantAddResponse)
def add_chant(chant: schemas.ChantLogCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Insert chant log
    db_chant = models.ChantLog(**chant.dict(), user_id=current_user.id)
    db.add(db_chant)
    
    # Upsert daily summary
    today = date.today()
    summary = db.query(models.DailySummary).filter(
        models.DailySummary.user_id == current_user.id,
        models.DailySummary.group_id == chant.group_id,
        models.DailySummary.chant_date == today
    ).first()
    
    if summary:
        summary.total_count += chant.count
    else:
        summary = models.DailySummary(
            user_id=current_user.id,
            group_id=chant.group_id,
            chant_date=today,
            total_count=chant.count
        )
        db.add(summary)
    
    db.commit()
    
    # Calculate totals for response
    today_total = summary.total_count
    all_time_total = db.query(func.sum(models.DailySummary.total_count)).filter(
        models.DailySummary.user_id == current_user.id,
        models.DailySummary.group_id == chant.group_id
    ).scalar_one_or_none() or 0
    
    return {"today_total": today_total, "all_time_total": all_time_total}

@router.get("/today", response_model=schemas.TodayChantResponse)
def get_today_chants(group_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    today_count = db.query(models.DailySummary.total_count).filter(
        models.DailySummary.user_id == current_user.id,
        models.DailySummary.group_id == group_id,
        models.DailySummary.chant_date == today
    ).scalar() or 0
    
    yesterday_count = db.query(models.DailySummary.total_count).filter(
        models.DailySummary.user_id == current_user.id,
        models.DailySummary.group_id == group_id,
        models.DailySummary.chant_date == yesterday
    ).scalar() or 0
    
    return {"today_count": today_count, "yesterday_count": yesterday_count}

@router.get("/history", response_model=List[schemas.DailySummary])
def get_chant_history(group_id: str, limit: int = Query(30, ge=1, le=365), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.DailySummary).filter(
        models.DailySummary.user_id == current_user.id,
        models.DailySummary.group_id == group_id
    ).order_by(models.DailySummary.chant_date.desc()).limit(limit).all()

@router.get("/group/{group_id}", response_model=schemas.GroupStatsResponse)
def get_group_stats(group_id: str, db: Session = Depends(database.get_db)):
    total_chants = db.query(func.sum(models.DailySummary.total_count)).filter(
        models.DailySummary.group_id == group_id
    ).scalar() or 0
    
    member_count = db.query(func.count(models.UserGroup.id)).filter(
        models.UserGroup.group_id == group_id
    ).scalar() or 0
    
    daily_total = db.query(func.sum(models.DailySummary.total_count)).filter(
        models.DailySummary.group_id == group_id,
        models.DailySummary.chant_date == date.today()
    ).scalar() or 0
    
    return {
        "total_chants": total_chants,
        "member_count": member_count,
        "daily_total": daily_total
    }

@router.get("/global", response_model=schemas.GlobalStatsResponse)
def get_global_stats(db: Session = Depends(database.get_db)):
    total_chants = db.query(func.sum(models.DailySummary.total_count)).scalar() or 0
    
    # Global target could be the sum of all group targets
    global_target = db.query(func.sum(models.Group.target_count)).filter(
        models.Group.is_active == True
    ).scalar() or 1 # Avoid division by zero
    
    completion_percentage = (total_chants / global_target) * 100 if global_target > 0 else 0
    
    return {
        "total_chants": total_chants,
        "global_target": global_target,
        "completion_percentage": round(completion_percentage, 2)
    }
