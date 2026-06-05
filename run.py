from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from backend.config import settings
from backend.logging_config import logger
from backend.modeles.database import Base, SessionLocal, engine
from backend.modeles.redis_client import close_redis, get_redis
from backend.routers import auth
from backend.routers.auth import limiter


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы БД созданы / проверены")
    yield
    await close_redis()
    logger.info("Redis соединение закрыто")


app = FastAPI(
    title="Agronomist API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

from backend.routers import weather, fields, calculator

app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(weather.router, prefix="/api", tags=["Weather"])
app.include_router(fields.router, prefix="/api", tags=["Fields"])
app.include_router(calculator.router, prefix="/api", tags=["Calculator"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    health = {"status": "ok", "postgres": "ok", "redis": "ok"}

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        health["postgres"] = f"error: {str(e)}"
        health["status"] = "degraded"
        logger.error(f"Health check — PostgreSQL error: {e}")

    try:
        redis = await get_redis()
        await redis.ping()
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"
        logger.error(f"Health check — Redis error: {e}")

    return health
