import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
# Жесткое ограничение на уровне сессии: все транзакции только для чтения
engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-c default_transaction_read_only=on"},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()