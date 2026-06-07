"""Shared user resolution — avoids AttributeError when user missing."""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from backend.encryption.security import get_current_user
from backend.modeles.database import get_db
from backend.modeles.models import User


def get_current_user_id(
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user.id
