from sqlalchemy import Column, Integer, Text, String, Numeric, DateTime, Date, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
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

class Bol(Base):
    __tablename__ = "bols"

    id                    = Column(Integer, primary_key=True, index=True)
    bill_id               = Column(Integer, ForeignKey("bills.id", ondelete="SET NULL"), nullable=True)
    bol_number            = Column(Text, nullable=True)
    shipper               = Column(Text, nullable=True)
    consignee             = Column(Text, nullable=True)
    notify_parties        = Column(JSONB, default=[])
    discharge_agent       = Column(Text, nullable=True)
    vessel_voyage         = Column(Text, nullable=True)
    port_of_loading       = Column(Text, nullable=True)
    place_of_receipt      = Column(Text, nullable=True)
    booking_ref           = Column(Text, nullable=True)
    port_of_discharge     = Column(Text, nullable=True)
    place_of_delivery     = Column(Text, nullable=True)
    shipped_on_board_date = Column(Date, nullable=True)
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
    updated_at            = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bill       = relationship("Bill", backref="bol")
    containers = relationship("BolContainer", back_populates="bol", cascade="all, delete-orphan")


class BolContainer(Base):
    __tablename__ = "bol_containers"

    id                 = Column(Integer, primary_key=True, index=True)
    bol_id             = Column(Integer, ForeignKey("bols.id", ondelete="CASCADE"), nullable=False)
    container_number   = Column(Text, nullable=True)
    seal_number        = Column(Text, nullable=True)
    marks_and_numbers  = Column(Text, nullable=True)
    description        = Column(Text, nullable=True)
    gross_cargo_weight = Column(Text, nullable=True)
    measurement        = Column(Text, nullable=True)

    bol = relationship("Bol", back_populates="containers")
