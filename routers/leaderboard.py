from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas, database

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("/global")
def get_global_leaderboard(db: Session = Depends(database.get_db)):
    results = db.query(
        models.User.name,
        func.sum(models.DailySummary.total_count).label("total")
    ).join(models.DailySummary).group_by(models.User.id).order_by(func.sum(models.DailySummary.total_count).desc()).limit(10).all()

    return [{"name": r.name, "count": r.total} for r in results]

@router.get("/group/{group_id}")
def get_group_leaderboard(group_id: str, db: Session = Depends(database.get_db)):
    results = db.query(
        models.User.name,
        func.sum(models.DailySummary.total_count).label("total")
    ).join(models.DailySummary).filter(models.DailySummary.group_id == group_id).group_by(models.User.id).order_by(func.sum(models.DailySummary.total_count).desc()).limit(10).all()

    return [{"name": r.name, "count": r.total} for r in results]
