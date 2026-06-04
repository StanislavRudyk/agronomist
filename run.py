import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.modeles.database import Base, engine
from backend.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agronomist API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api", tags=["Auth"])
