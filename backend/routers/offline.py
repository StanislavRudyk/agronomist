from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.modeles.database import get_db
from backend.routers.auth import get_current_user
from backend.modeles.models import User
from backend.services.offline_service import OfflineService

router = APIRouter()

def _get_user_id(db: Session, user_email: str) -> int:
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user.id

@router.get("/offline/snapshot", summary="Полный снапшот всех данных пользователя для оффлайна")
async def get_snapshot(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return OfflineService.generate_snapshot(db, _get_user_id(db, user_email))

@router.post("/offline/sync", summary="Синхронизация пакета операций после оффлайна")
async def sync_operations(
    operations: List[dict],
    db: Session = Depends(get_db),
    user_email: str = Depends(get_current_user)
):
    return OfflineService.sync_operations(db, _get_user_id(db, user_email), operations)
