import os, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.models import Bill
from api.queue import publish_bill_message
from api.schemas import BillResponse, BillUpdate, UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_bill(file: UploadFile = File(...), llm_engine: str = Form(...), db: AsyncSession = Depends(get_db)):
    if llm_engine not in ("ollama", "gemini"):
        raise HTTPException(status_code=400, detail="llm_engine must be 'ollama' or 'gemini'.")

    file_type = "pdf" if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf") else "image"
    uploads_dir = Path(os.getenv("UPLOADS_DIR", "./uploads")).resolve()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = str(uploads_dir / f"{uuid.uuid4().hex}_{Path(file.filename or 'doc').name}")
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    bill = Bill(file_path=file_path, file_type=file_type, llm_engine=llm_engine, status="PENDING")
    db.add(bill)
    await db.commit()
    await db.refresh(bill)

    try:
        publish_bill_message(bill.id, file_path, file_type, llm_engine)
    except Exception as exc:
        pass

    return UploadResponse(bill_id=bill.id)

@router.get("", response_model=List[BillResponse])
async def list_bills(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Bill).order_by(Bill.created_at.desc()))
    return res.scalars().all()

@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(bill_id: int, db: AsyncSession = Depends(get_db)):
    b = await db.get(Bill, bill_id)
    if not b: raise HTTPException(status_code=404, detail="Bill not found.")
    return b

@router.put("/{bill_id}", response_model=BillResponse)
async def update_bill(bill_id: int, bill_update: BillUpdate, db: AsyncSession = Depends(get_db)):
    bill = await db.get(Bill, bill_id)
    if not bill: raise HTTPException(status_code=404, detail="Bill not found.")
    for f, v in bill_update.model_dump(exclude_unset=True).items():
        setattr(bill, f, v)
    bill.status = "REVIEWED"
    bill.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(bill)
    return bill

@router.get("/{bill_id}/file")
async def serve_bill_file(bill_id: int, db: AsyncSession = Depends(get_db)):
    bill = await db.get(Bill, bill_id)
    if not bill or not Path(bill.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(bill.file_path)
