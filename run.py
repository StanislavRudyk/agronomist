import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import redis
from backend.modeles.database import engine, Base
from backend.modeles import models

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Agronomist API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


