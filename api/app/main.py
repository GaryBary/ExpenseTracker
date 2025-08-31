import os
from datetime import datetime, timezone, date as dtdate
import pytz
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from .database import Base, engine, SessionLocal, DB_SCHEMA
from . import models
from .ocr_providers.ocr_space import ocr_space_image
from .utils.fy import fy_range_for_date

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Expense Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Ensure the Postgres schema exists, then create tables
if engine.dialect.name == "postgresql":
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
Base.metadata.create_all(bind=engine)

@app.post("/expenses")
async def create_expense(
    image: UploadFile | None = File(default=None),
    description: str | None = Form(default=None),
    vendor: str | None = Form(default=None),
    date: str | None = Form(default=None),  # YYYY-MM-DD
    amount_cents: int | None = Form(default=None),
    category: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not image and not (description or vendor or amount_cents or date):
        raise HTTPException(400, "Provide an image or manual fields.")
    image_bytes = await image.read() if image else None

    ocr_text = None
    if image_bytes:
        api_key = os.getenv("OCR_SPACE_API_KEY")
        if not api_key:
            raise HTTPException(500, "OCR_SPACE_API_KEY not configured")
        ocr_text = ocr_space_image(image_bytes, api_key)

    tz = pytz.timezone(os.getenv("APP_TZ", "Australia/Sydney"))
    created_at = datetime.now(tz).astimezone(timezone.utc)

    exp = models.Expense(
        created_at=created_at,
        date=dtdate.fromisoformat(date) if date else None,
        amount_cents=amount_cents,
        currency=os.getenv("APP_CURRENCY", "AUD"),
        description=description,
        vendor=vendor,
        category=category,
        image_bytes=image_bytes,
        ocr_text=ocr_text,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return {"id": str(exp.id)}

@app.get("/expenses")
def list_expenses(
    q: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Expense)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Expense.description.ilike(like)) |
            (models.Expense.vendor.ilike(like)) |
            (models.Expense.ocr_text.ilike(like))
        )
    if start_date:
        query = query.filter(models.Expense.date >= dtdate.fromisoformat(start_date))
    if end_date:
        query = query.filter(models.Expense.date <= dtdate.fromisoformat(end_date))
    rows = query.order_by(models.Expense.date.desc()).limit(200).all()
    return [
        {
            "id": str(e.id),
            "date": e.date.isoformat() if e.date else None,
            "amount_cents": e.amount_cents
