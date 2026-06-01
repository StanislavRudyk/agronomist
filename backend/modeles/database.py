import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB")


SQLALCHEMY_DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}/{PG_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

