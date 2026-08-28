from sqlalchemy import Column, Integer, Text, String, Numeric, DateTime, Date, func
from sqlalchemy.dialects.postgresql import JSONB
from api.db import Base

class Bill(Base):
    __tablename__ = "bills"

    id             = Column(Integer, primary_key=True, index=True)
    file_path      = Column(Text,        nullable=False)
    file_type      = Column(String(10),  nullable=False)
    llm_engine     = Column(String(20),  nullable=False)
    status         = Column(String(20),  nullable=False, default="PENDING")
    vendor_name    = Column(Text,        nullable=True)
    vendor_address = Column(Text,        nullable=True)
    invoice_number = Column(Text,        nullable=True)
    invoice_date   = Column(Date,        nullable=True)
    due_date       = Column(Date,        nullable=True)
    currency       = Column(String(10),  nullable=True)
    line_items     = Column(JSONB,       nullable=True)
    subtotal       = Column(Numeric(12, 2), nullable=True)
    tax_amount     = Column(Numeric(12, 2), nullable=True)
    discount       = Column(Numeric(12, 2), nullable=True)
    total_amount   = Column(Numeric(12, 2), nullable=True)
    payment_method = Column(Text,        nullable=True)
    notes          = Column(Text,        nullable=True)
    error_message  = Column(Text,        nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
