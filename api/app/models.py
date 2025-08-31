import uuid
from sqlalchemy import Column, String, Date, Integer, LargeBinary, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
try:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
except Exception:
    from sqlalchemy import JSON as JSONType
from .database import Base

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False)
    date = Column(Date, nullable=True)
    amount_cents = Column(Integer, nullable=True)
    currency = Column(String(8), nullable=False, default="AUD")
    description = Column(Text, nullable=True)
    vendor = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    image_bytes = Column(LargeBinary, nullable=True)
    ocr_text = Column(Text, nullable=True)
    meta = Column(JSONType, nullable=True)
