from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.modeles.database import get_db
from backend.modeles.models import Field, User
from backend.modeles.schemas import FieldCreate, FieldResponse
from backend.routers.auth import get_current_user

router = APIRouter()

@router.post("/fields", response_model=FieldResponse, summary="Создать новое поле")
async def create_field(
    field_data: FieldCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db_field = Field(
        user_id=user.id,
        name=field_data.name,
        latitude=field_data.latitude,
        longitude=field_data.longitude,
        crop_type=field_data.crop_type
    )
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field

@router.get("/fields", response_model=list[FieldResponse], summary="Получить список полей")
async def get_fields(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return db.query(Field).filter(Field.user_id == user.id).all()
