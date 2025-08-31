import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Use psycopg (v3) driver explicitly.
# Render often provides URLs like "postgres://..." or "postgresql://..."
# Rewrite to "postgresql+psycopg://..." so SQLAlchemy imports the right driver.
if DATABASE_URL.startswith("postgres://"):
	DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
	DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

DB_SCHEMA = os.getenv("DB_SCHEMA", "et")
metadata = MetaData(schema=DB_SCHEMA)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base(metadata=metadata)
