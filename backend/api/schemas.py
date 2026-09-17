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

class BolContainerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:                 int
    container_number:   Optional[str] = None
    seal_number:        Optional[str] = None
    marks_and_numbers:  Optional[str] = None
    description:        Optional[str] = None
    gross_cargo_weight: Optional[str] = None
    measurement:        Optional[str] = None

class BolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:                    int
    bill_id:               Optional[int] = None
    bol_number:            Optional[str] = None
    shipper:               Optional[str] = None
    consignee:             Optional[str] = None
    notify_parties:        Optional[List[str]] = None
    discharge_agent:       Optional[str] = None
    vessel_voyage:         Optional[str] = None
    port_of_loading:       Optional[str] = None
    place_of_receipt:      Optional[str] = None
    booking_ref:           Optional[str] = None
    port_of_discharge:     Optional[str] = None
    place_of_delivery:     Optional[str] = None
    shipped_on_board_date: Optional[date] = None
    containers:            List[BolContainerResponse] = []
    file_path:             Optional[str] = None
    file_type:             Optional[str] = None
    llm_engine:            Optional[str] = None
    status:                Optional[str] = None
    error_message:         Optional[str] = None
    created_at:            Optional[datetime] = None
    updated_at:            Optional[datetime] = None

class BolContainerUpdate(BaseModel):
    id:                 Optional[int] = None
    container_number:   Optional[str] = None
    seal_number:        Optional[str] = None
    marks_and_numbers:  Optional[str] = None
    description:        Optional[str] = None
    gross_cargo_weight: Optional[str] = None
    measurement:        Optional[str] = None

class BolUpdate(BaseModel):
    bol_number:            Optional[str] = None
    shipper:               Optional[str] = None
    consignee:             Optional[str] = None
    notify_parties:        Optional[List[str]] = None
    discharge_agent:       Optional[str] = None
    vessel_voyage:         Optional[str] = None
    port_of_loading:       Optional[str] = None
    place_of_receipt:      Optional[str] = None
    booking_ref:           Optional[str] = None
    port_of_discharge:     Optional[str] = None
    place_of_delivery:     Optional[str] = None
    shipped_on_board_date: Optional[date] = None
    containers:            Optional[List[BolContainerUpdate]] = None
