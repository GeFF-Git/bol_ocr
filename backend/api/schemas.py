from __future__ import annotations
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict

class BillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             int
    file_path:      str
    file_type:      str
    llm_engine:     str
    status:         str
    vendor_name:    Optional[str]   = None
    vendor_address: Optional[str]   = None
    invoice_number: Optional[str]   = None
    invoice_date:   Optional[date]  = None
    due_date:       Optional[date]  = None
    currency:       Optional[str]   = None
    line_items:     Optional[List[Any]] = None
    subtotal:       Optional[float] = None
    tax_amount:     Optional[float] = None
    discount:       Optional[float] = None
    total_amount:   Optional[float] = None
    payment_method: Optional[str]   = None
    notes:          Optional[str]   = None
    error_message:  Optional[str]   = None
    created_at:     Optional[datetime] = None
    updated_at:     Optional[datetime] = None

class UploadResponse(BaseModel):
    bill_id: int
    status:  str = "PENDING"

class BillUpdate(BaseModel):
    vendor_name:    Optional[str]       = None
    vendor_address: Optional[str]       = None
    invoice_number: Optional[str]       = None
    invoice_date:   Optional[date]      = None
    due_date:       Optional[date]      = None
    currency:       Optional[str]       = None
    line_items:     Optional[List[Any]] = None
    subtotal:       Optional[float]     = None
    tax_amount:     Optional[float]     = None
    discount:       Optional[float]     = None
    total_amount:   Optional[float]     = None
    payment_method: Optional[str]       = None
    notes:          Optional[str]       = None
