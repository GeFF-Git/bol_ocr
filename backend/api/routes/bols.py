from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from api.db import get_db
from api.models import Bill, Bol, BolContainer
from api.schemas import BolResponse, BolUpdate

router = APIRouter()

def _bol_to_response(bol: Bol) -> dict:
    """Convert a Bol ORM object to a dict that BolResponse can consume."""
    d = {
        "id": bol.id,
        "bill_id": bol.bill_id,
        "bol_number": bol.bol_number,
        "shipper": bol.shipper,
        "consignee": bol.consignee,
        "notify_parties": bol.notify_parties or [],
        "discharge_agent": bol.discharge_agent,
        "vessel_voyage": bol.vessel_voyage,
        "port_of_loading": bol.port_of_loading,
        "place_of_receipt": bol.place_of_receipt,
        "booking_ref": bol.booking_ref,
        "port_of_discharge": bol.port_of_discharge,
        "place_of_delivery": bol.place_of_delivery,
        "shipped_on_board_date": bol.shipped_on_board_date,
        "containers": bol.containers,
        "created_at": bol.created_at,
        "updated_at": bol.updated_at,
    }
    # Join bill fields if available
    if bol.bill:
        d["file_path"] = bol.bill.file_path
        d["file_type"] = bol.bill.file_type
        d["llm_engine"] = bol.bill.llm_engine
        d["status"] = bol.bill.status
        d["error_message"] = bol.bill.error_message
    return d


@router.get("", response_model=List[BolResponse])
async def list_bols(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Bol).options(selectinload(Bol.containers), selectinload(Bol.bill)).order_by(Bol.created_at.desc())
    )
    bols = res.scalars().all()
    return [_bol_to_response(b) for b in bols]


@router.get("/{bol_id}", response_model=BolResponse)
async def get_bol(bol_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Bol).options(selectinload(Bol.containers), selectinload(Bol.bill)).where(Bol.id == bol_id)
    )
    bol = res.scalars().first()
    if not bol:
        raise HTTPException(status_code=404, detail="BOL not found.")
    return _bol_to_response(bol)


@router.get("/by-bill/{bill_id}", response_model=BolResponse)
async def get_bol_by_bill(bill_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Bol).options(selectinload(Bol.containers), selectinload(Bol.bill)).where(Bol.bill_id == bill_id)
    )
    bol = res.scalars().first()
    if not bol:
        raise HTTPException(status_code=404, detail="No BOL found for this bill.")
    return _bol_to_response(bol)


@router.put("/{bol_id}", response_model=BolResponse)
async def update_bol(bol_id: int, bol_update: BolUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Bol).options(selectinload(Bol.containers), selectinload(Bol.bill)).where(Bol.id == bol_id)
    )
    bol = res.scalars().first()
    if not bol:
        raise HTTPException(status_code=404, detail="BOL not found.")

    # Update BOL-level fields
    update_data = bol_update.model_dump(exclude_unset=True, exclude={"containers"})
    for field, value in update_data.items():
        setattr(bol, field, value)
    bol.updated_at = datetime.now(timezone.utc)

    # Replace containers if provided
    if bol_update.containers is not None:
        # Delete existing containers
        for c in list(bol.containers):
            await db.delete(c)
        await db.flush()
        # Insert new containers
        for c_data in bol_update.containers:
            container = BolContainer(
                bol_id=bol.id,
                container_number=c_data.container_number,
                seal_number=c_data.seal_number,
                marks_and_numbers=c_data.marks_and_numbers,
                description=c_data.description,
                gross_cargo_weight=c_data.gross_cargo_weight,
                measurement=c_data.measurement,
            )
            db.add(container)

    # Mark parent bill as REVIEWED
    if bol.bill:
        bol.bill.status = "REVIEWED"
        bol.bill.updated_at = datetime.now(timezone.utc)

    await db.commit()

    # Re-fetch with relationships
    res = await db.execute(
        select(Bol).options(selectinload(Bol.containers), selectinload(Bol.bill)).where(Bol.id == bol_id)
    )
    bol = res.scalars().first()
    return _bol_to_response(bol)
