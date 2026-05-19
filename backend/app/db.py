from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://cliniciq2_user:cliniciq2_pass@db:5433/cliniciq2_db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-c default_transaction_read_only=on"},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()