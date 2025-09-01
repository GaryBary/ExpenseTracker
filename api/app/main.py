import os
from datetime import datetime, timezone, date as dtdate
import pytz
from PIL import Image
import io
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from .database import Base, engine, SessionLocal, DB_SCHEMA
from . import models
from .ocr_providers.ocr_space import ocr_space_image
from .utils.fy import fy_range_for_date
from .utils.parse_receipt import parse_receipt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def compress_image(image_bytes: bytes, max_size_kb: int = 800) -> bytes:
    """Compress image to stay under the size limit"""
    try:
        # Open the image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles PNG, etc.)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Start with 85% quality
        quality = 85
        
        while True:
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_size = output.tell()
            
            # If under size limit, return
            if compressed_size <= max_size_kb * 1024:
                return output.getvalue()
            
            # Reduce quality and try again
            quality -= 10
            if quality < 30:
                # If still too big, resize the image
                width, height = image.size
                image = image.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
                quality = 85
                
            if quality < 10:
                break
                
        return output.getvalue()
    except Exception as e:
        # If compression fails, return original
        return image_bytes

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
    parsed_date = None
    parsed_amount_cents = None
    parsed_vendor = None
    parsed_description = None
    parsed_category = None
    
    if image_bytes:
        api_key = os.getenv("OCR_SPACE_API_KEY")
        if not api_key:
            raise HTTPException(500, "OCR_SPACE_API_KEY not configured")
        
        # Compress image before OCR
        compressed_image = compress_image(image_bytes)
        ocr_text = ocr_space_image(compressed_image, api_key)
        
        # Parse OCR text to extract fields
        if ocr_text:
            parsed_date, parsed_amount_cents, parsed_vendor, parsed_description, parsed_category = parse_receipt(ocr_text)

    tz = pytz.timezone(os.getenv("APP_TZ", "Australia/Sydney"))
    created_at = datetime.now(tz).astimezone(timezone.utc)

    exp = models.Expense(
        created_at=created_at,
        date=dtdate.fromisoformat(date) if date else parsed_date,
        amount_cents=amount_cents or parsed_amount_cents,
        currency=os.getenv("APP_CURRENCY", "AUD"),
        description=description or parsed_description,
        vendor=vendor or parsed_vendor,
        category=category or parsed_category,
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
            "amount_cents": e.amount_cents,
            "currency": e.currency,
            "description": e.description,
            "vendor": e.vendor,
            "category": e.category,
        }
        for e in rows
    ]

@app.get("/expenses/{expense_id}")
def get_expense(expense_id: str, db: Session = Depends(get_db)):
    e = db.get(models.Expense, expense_id)
    if not e:
        raise HTTPException(404, "Not found")
    return {
        "id": str(e.id),
        "date": e.date.isoformat() if e.date else None,
        "amount_cents": e.amount_cents,
        "currency": e.currency,
        "description": e.description,
        "vendor": e.vendor,
        "category": e.category,
        "ocr_text": e.ocr_text,
    }

@app.get("/stats/fy")
def stats_fy(db: Session = Depends(get_db)):
    today = datetime.now().date()
    start, end, label = fy_range_for_date(today)
    total = db.query(func.coalesce(func.sum(models.Expense.amount_cents), 0)).filter(
        models.Expense.date >= start, models.Expense.date <= end
    ).scalar() or 0
    by_cat = (
        db.query(models.Expense.category, func.coalesce(func.sum(models.Expense.amount_cents), 0))
        .filter(models.Expense.date >= start, models.Expense.date <= end)
        .group_by(models.Expense.category)
        .all()
    )
    return {
        "fy": label,
        "total_cents": int(total),
        "by_category": [{"category": c or "Uncategorized", "total_cents": int(s)} for c, s in by_cat],
    }
