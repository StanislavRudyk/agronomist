from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.config import settings
from backend.encryption.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from backend.logging_config import security_logger
from backend.modeles import models
from backend.modeles.database import get_db
from backend.modeles.redis_client import get_redis
from backend.modeles.schemas import (
    MessageResponse,
    RefreshTokenRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        security_logger.warning(f"Попытка регистрации с существующим email: {user.email}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Этот email уже занят!")

    hashed_pw = get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pw)

    db.add(new_user)
    from sqlalchemy.exc import IntegrityError
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        security_logger.warning(f"Race condition: регистрация существующего email: {user.email}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Этот email уже занят!")

    security_logger.info(f"Новый пользователь зарегистрирован: {user.email}")
    return new_user


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(user: UserLogin, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        security_logger.warning(f"Неудачная попытка входа: {user.email} | IP: {request.client.host}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль!")

    access_token = create_access_token(data={"sub": db_user.email})
    refresh_token, jti = create_refresh_token(data={"sub": db_user.email})

    # Сохраняем jti refresh токена в Redis с TTL = REFRESH_TOKEN_EXPIRE_DAYS
    redis = await get_redis()
    await redis.setex(
        f"refresh_token:{jti}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        db_user.email,
    )

    security_logger.info(f"Успешный вход: {db_user.email} | IP: {request.client.host}")
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(body: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """Обновление пары токенов по refresh token."""
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный тип токена")

    jti = payload.get("jti")
    email = payload.get("sub")
    if not jti or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен")

    # Проверяем что refresh token ещё валиден в Redis (не отозван)
    redis = await get_redis()
    stored_email = await redis.get(f"refresh_token:{jti}")
    if stored_email is None:
        security_logger.warning(f"Попытка использовать отозванный refresh token: {email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отозван или истёк")

    # Проверяем что пользователь ещё существует
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        await redis.delete(f"refresh_token:{jti}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")

    # Ротация: удаляем старый refresh token, создаём новую пару
    await redis.delete(f"refresh_token:{jti}")

    new_access = create_access_token(data={"sub": email})
    new_refresh, new_jti = create_refresh_token(data={"sub": email})

    await redis.setex(
        f"refresh_token:{new_jti}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        email,
    )

    security_logger.info(f"Токены обновлены: {email}")
    return TokenPair(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshTokenRequest, current_user: str = Depends(get_current_user)):
    """Отзыв refresh token — пользователь больше не сможет обновить токены."""
    payload = decode_token(body.refresh_token)
    if payload.get("sub") != current_user:
        raise HTTPException(status_code=403, detail="Refresh token не принадлежит текущему пользователю")
    jti = payload.get("jti")

    if jti:
        redis = await get_redis()
        await redis.delete(f"refresh_token:{jti}")
        security_logger.info(f"Logout: {current_user}")

    return MessageResponse(detail="Выход выполнен успешно")


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user
