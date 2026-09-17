# BOL Extraction, Persistence & Review/Edit — Implementation Plan

## Background

The current codebase is a **generic bill/invoice processor**. The DB schema, extraction prompt, API contracts, and frontend are all built around invoice fields (vendor_name, vendor_address, invoice_number, line_items, subtotal, tax_amount, etc.). This task converts it to a **Bill of Lading (BOL) processor** with a completely different field structure.

## User Review Required

> [!IMPORTANT]
> **The old `bills` table stays as-is.** Per your instructions, we do NOT migrate or backfill existing records. The old `bills` table and its invoice-specific columns remain untouched. New BOL records will be stored in a **new `bols` table** with the BOL-specific fields, plus a child `bol_containers` table. The existing `bills` table columns (vendor_name, invoice_number, subtotal, etc.) are unrelated to BOL fields and will NOT be repurposed.

> [!IMPORTANT]
> **No router/SPA library exists currently.** The frontend is a single-page app with no React Router. To add the Review/Edit page and BOL History view, I will add `react-router-dom` to support page navigation (Dashboard → History → Review/Edit). This is the minimal change needed to support the "reachable from a list/history view" requirement.

> [!WARNING]
> **The existing `BillDetailPanel` (invoice edit modal) will remain functional** for any old invoice-type records. The new BOL Review/Edit page is a separate new page/component. The existing upload flow + detail panel for invoices won't be broken.

## Open Questions

> [!IMPORTANT]
> **1. Should the Upload page offer a "BOL" document type toggle?**
> Currently the upload form only asks for LLM engine (Ollama/Gemini). Since we're adding BOL extraction alongside the existing invoice extraction, should the upload form let the user pick "Invoice" vs "BOL" document type? Or should we assume **all future uploads are BOLs** and the old invoice flow is deprecated?
> **My recommendation**: Add a document-type selector (`invoice` | `bol`) to the upload form. If the user selects `bol`, the consumer uses the new BOL prompt and writes to the `bols`/`bol_containers` tables. If `invoice`, it uses the existing flow unchanged. This keeps backward compatibility.

> [!IMPORTANT]
> **2. Should Notify Parties be stored as JSONB array or a child table?**
> Since notify parties is a simple array of strings (not structured objects), and the rest of the schema uses JSONB for array data (e.g., the old `line_items`), I recommend **JSONB array** on the `bols` table. This avoids a third table for what is essentially a list of names. If you prefer a normalized child table, let me know.

> [!IMPORTANT]
> **3. Shipped on Board Date format.**
> The sample BOLs show dates like "01-OCT-2020", "20-Aug-2020", "03-Apr-2025". The extraction prompt will request `YYYY-MM-DD` format (same convention as the existing prompt). The DB column will be `DATE` type. OK?

---

## Proposed Changes

### Database Schema

#### [NEW] `bols` table (BOL-level fields 1–12)

```sql
CREATE TABLE IF NOT EXISTS bols (
    id                    SERIAL PRIMARY KEY,
    bill_id               INTEGER REFERENCES bills(id) ON DELETE SET NULL,
    -- Links to the parent bills row for file_path, file_type, llm_engine, status
    bol_number            TEXT,                          -- 1. Bill of Lading No.
    shipper               TEXT,                          -- 2. Shipper
    consignee             TEXT,                          -- 3. Consignee
    notify_parties        JSONB DEFAULT '[]'::jsonb,     -- 4. Array of strings
    discharge_agent       TEXT,                          -- 5. Port of Discharge Agent
    vessel_voyage         TEXT,                          -- 6. Vessel and Voyage No.
    port_of_loading       TEXT,                          -- 7. Port of Loading
    place_of_receipt      TEXT,                          -- 8. Place of Receipt
    booking_ref           TEXT,                          -- 9. Booking Ref.
    port_of_discharge     TEXT,                          -- 10. Port of Discharge
    place_of_delivery     TEXT,                          -- 11. Place of Delivery
    shipped_on_board_date DATE,                          -- 12. Shipped on Board Date
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### [NEW] `bol_containers` table (Container-level fields 13–18)

```sql
CREATE TABLE IF NOT EXISTS bol_containers (
    id                  SERIAL PRIMARY KEY,
    bol_id              INTEGER NOT NULL REFERENCES bols(id) ON DELETE CASCADE,
    container_number    TEXT,                          -- 13. Container Number
    seal_number         TEXT,                          -- 14. Seal Number
    marks_and_numbers   TEXT,                          -- 15. Marks and Numbers
    description         TEXT,                          -- 16. Description of Packages and Goods
    gross_cargo_weight  TEXT,                          -- 17. Gross Cargo Weight (text to preserve units)
    measurement         TEXT                           -- 18. Measurement (text to preserve units)
);
```

> [!NOTE]
> `gross_cargo_weight` and `measurement` are stored as `TEXT` rather than `NUMERIC` because BOL documents include units inline (e.g., "26,000.000 kgs.", "68.000cu. m.") and we want to preserve the exact value as extracted. The UI can display the raw string and the user can correct it.

> [!NOTE]
> The `bols.bill_id` FK links back to the existing `bills` table row, which holds `file_path`, `file_type`, `llm_engine`, `status`, and `error_message`. This avoids duplicating those infrastructure columns. The consumer will continue to update `bills.status` to `PROCESSED`/`FAILED`, and the BOL-specific data goes into `bols` + `bol_containers`.

---

### Extraction Prompt

#### [MODIFY] [extraction_prompt.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/prompts/extraction_prompt.py)

Add a new `BOL_EXTRACTION_PROMPT` constant alongside the existing `EXTRACTION_PROMPT` (which remains unchanged for invoice processing). The new prompt will:

- Follow the same style: role statement → task description → "Return ONLY a valid JSON object" → schema template
- Request all 18 fields in a flat+nested structure
- Mandate `containers` as a JSON array (even for single container)
- Mandate `notify_parties` as a JSON array of strings
- Explicitly state: "If a field is not present or not legible, return null. Do not guess or hallucinate."

**New prompt schema:**
```json
{
  "bol_number": "string or null",
  "shipper": "string or null",
  "consignee": "string or null",
  "notify_parties": ["string"],
  "discharge_agent": "string or null",
  "vessel_voyage": "string or null",
  "port_of_loading": "string or null",
  "place_of_receipt": "string or null",
  "booking_ref": "string or null",
  "port_of_discharge": "string or null",
  "place_of_delivery": "string or null",
  "shipped_on_board_date": "YYYY-MM-DD or null",
  "containers": [
    {
      "container_number": "string or null",
      "seal_number": "string or null",
      "marks_and_numbers": "string or null",
      "description": "string or null",
      "gross_cargo_weight": "string or null",
      "measurement": "string or null"
    }
  ]
}
```

---

### Extractors

#### [MODIFY] [gemini_extractor.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/extractors/gemini_extractor.py)

- `extract()` method gains an optional `prompt` parameter (defaults to `EXTRACTION_PROMPT` for backward compat)
- When called for BOL extraction, the consumer passes `BOL_EXTRACTION_PROMPT`

#### [MODIFY] [ollama_extractor.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/extractors/ollama_extractor.py)

- Same change: `extract()` gains an optional `prompt` parameter

#### [MODIFY] [base.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/extractors/base.py)

- Update abstract method signature to accept optional `prompt` parameter

---

### Consumer Worker

#### [MODIFY] [consumer.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/worker/consumer.py)

Major changes:

1. **Read `doc_type` from the RabbitMQ message** (`"invoice"` or `"bol"`). If not present, default to `"invoice"` for backward compatibility.

2. **Branch on `doc_type`**:
   - `"invoice"` → existing flow (unchanged)
   - `"bol"` → use `BOL_EXTRACTION_PROMPT`, parse BOL JSON, validate, write to `bols` + `bol_containers`

3. **BOL validation logic**:
   - Verify `containers` is a list (coerce single object to list)
   - Verify `notify_parties` is a list (coerce single string to list)
   - Log warnings for missing required keys but proceed (don't drop data)
   - Wrap container inserts in a transaction with the BOL insert

4. **BOL persistence flow**:
   ```
   INSERT INTO bols (...) VALUES (...) RETURNING id
   for each container:
       INSERT INTO bol_containers (bol_id, ...) VALUES (...)
   UPDATE bills SET status='PROCESSED' WHERE id=bill_id
   ```

---

### RabbitMQ Message Contract

#### [MODIFY] [queue.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/api/queue.py)

Add `doc_type` to the published message:
```python
# Current: {"bill_id": 1, "file_path": "...", "file_type": "pdf", "llm_engine": "gemini"}
# New:     {"bill_id": 1, "file_path": "...", "file_type": "pdf", "llm_engine": "gemini", "doc_type": "bol"}
```

---

### SQLAlchemy Models

#### [MODIFY] [models.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/api/models.py)

Add two new model classes (existing `Bill` model unchanged):

```python
class Bol(Base):
    __tablename__ = "bols"
    id                    = Column(Integer, primary_key=True, index=True)
    bill_id               = Column(Integer, ForeignKey("bills.id", ondelete="SET NULL"), nullable=True)
    bol_number            = Column(Text)
    shipper               = Column(Text)
    consignee             = Column(Text)
    notify_parties        = Column(JSONB, default=[])
    discharge_agent       = Column(Text)
    vessel_voyage         = Column(Text)
    port_of_loading       = Column(Text)
    place_of_receipt      = Column(Text)
    booking_ref           = Column(Text)
    port_of_discharge     = Column(Text)
    place_of_delivery     = Column(Text)
    shipped_on_board_date = Column(Date)
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
    updated_at            = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bill       = relationship("Bill", backref="bol")
    containers = relationship("BolContainer", back_populates="bol", cascade="all, delete-orphan")

class BolContainer(Base):
    __tablename__ = "bol_containers"
    id                = Column(Integer, primary_key=True, index=True)
    bol_id            = Column(Integer, ForeignKey("bols.id", ondelete="CASCADE"), nullable=False)
    container_number  = Column(Text)
    seal_number       = Column(Text)
    marks_and_numbers = Column(Text)
    description       = Column(Text)
    gross_cargo_weight = Column(Text)
    measurement       = Column(Text)

    bol = relationship("Bol", back_populates="containers")
```

---

### Pydantic Schemas

#### [MODIFY] [schemas.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/api/schemas.py)

Add new schemas (existing schemas unchanged):

```python
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
    # Joined from bills table for convenience
    file_path:             Optional[str] = None
    file_type:             Optional[str] = None
    llm_engine:            Optional[str] = None
    status:                Optional[str] = None
    error_message:         Optional[str] = None
    created_at:            Optional[datetime] = None
    updated_at:            Optional[datetime] = None

class BolContainerUpdate(BaseModel):
    id:                 Optional[int] = None  # null for new containers
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
```

---

### API Routes

#### [MODIFY] [bills.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/api/routes/bills.py)

Add `doc_type` parameter to the upload endpoint:

```python
@router.post("/upload", ...)
async def upload_bill(
    file: UploadFile = File(...),
    llm_engine: str = Form(...),
    doc_type: str = Form("bol"),   # NEW: "invoice" or "bol", defaults to "bol"
    db: AsyncSession = Depends(get_db)
):
```

#### [NEW] [bols.py](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/api/routes/bols.py)

New router at `/api/bols` with these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/bols` | List all BOLs (with status, shipper, bol_number, dates) |
| `GET` | `/api/bols/{bol_id}` | Get single BOL with all containers |
| `GET` | `/api/bols/by-bill/{bill_id}` | Get BOL by its parent bill_id (for post-upload redirect) |
| `PUT` | `/api/bols/{bol_id}` | Update BOL fields + replace containers array |

The `PUT` endpoint will:
1. Update all BOL-level fields from `BolUpdate`
2. Delete existing containers and re-insert from the `containers` array (simpler than diffing, and container count is small)
3. Set `bills.status = 'REVIEWED'` on the parent bill

---

### Frontend

#### [NEW] `react-router-dom` dependency

Add to `package.json`. Wrap `<App>` in `<BrowserRouter>` with routes:
- `/` → Dashboard (existing BentoGrid)
- `/bols` → BOL History list
- `/bols/:bolId` → BOL Review/Edit page

#### [MODIFY] [App.jsx](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/frontend/src/App.jsx)

- Wrap in `<BrowserRouter>` with `<Routes>`
- Add nav bar with links to Dashboard and BOL History
- Keep existing dashboard functionality at `/`

#### [MODIFY] [UploadCard.jsx](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/frontend/src/components/UploadCard.jsx)

- Add document type toggle (Invoice / BOL)
- After successful BOL upload, poll for processing completion, then redirect to `/bols/:bolId` review page

#### [MODIFY] [client.js](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/frontend/src/api/client.js)

Add new API functions:
```javascript
export async function listBols() { ... }
export async function getBol(id) { ... }
export async function getBolByBillId(billId) { ... }
export async function updateBol(id, data) { ... }
```

#### [NEW] [BolHistoryPage.jsx](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/frontend/src/components/BolHistoryPage.jsx)

Minimal history view:
- Glassmorphic table/card-list showing: BOL No., Shipper, upload date, status
- Each row links to `/bols/:bolId` review page
- Consistent with existing design language

#### [NEW] [BolReviewPage.jsx](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/frontend/src/components/BolReviewPage.jsx)

Full BOL Review & Edit page:

**Layout:**
- Left half: BOL document image/PDF viewer (reusing existing pattern from `BillDetailPanel`)
- Right half: editable form

**BOL-level fields (grid layout, fields 1–12):**
- 4-column grid for short fields (BOL No., Booking Ref, Port of Loading, etc.)
- Full-width for longer fields (Shipper, Consignee, Discharge Agent)
- Notify Parties as a tag-style input (add/remove individual party strings)

**Container section (below BOL fields):**
- Repeatable card/row per container with all 6 sub-fields editable
- "Add Container" button
- "Remove" button per container row
- Visual separator between containers

**Actions:**
- "Save" button → `PUT /api/bols/:bolId` with full form state
- Loading spinner during save
- Success/error toast
- Visual flag (amber border) on empty required fields (bol_number, shipper)
- Back button to BOL History

---

### Migration Strategy

Since this project does **not** use Alembic or any migration tool (the schema is managed via a raw `schema.sql` file), I will:

1. **Add the new DDL to [schema.sql](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend/schema.sql)** — append the `CREATE TABLE IF NOT EXISTS bols` and `CREATE TABLE IF NOT EXISTS bol_containers` statements after the existing `bills` table. `IF NOT EXISTS` ensures it's safe to re-run.

2. **Also create a standalone migration script** `backend/migrate_add_bols.sql` that can be run once against an existing database to add the new tables without touching the `bills` table.

---

## File Change Summary

### Backend ([backend/](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/backend))

| Action | File | What changes |
|--------|------|-------------|
| MODIFY | `schema.sql` | Append `bols` and `bol_containers` table DDL |
| NEW | `migrate_add_bols.sql` | Standalone migration script |
| MODIFY | `prompts/extraction_prompt.py` | Add `BOL_EXTRACTION_PROMPT` |
| MODIFY | `extractors/base.py` | Add optional `prompt` param to `extract()` |
| MODIFY | `extractors/gemini_extractor.py` | Accept `prompt` param |
| MODIFY | `extractors/ollama_extractor.py` | Accept `prompt` param |
| MODIFY | `api/models.py` | Add `Bol` and `BolContainer` models |
| MODIFY | `api/schemas.py` | Add BOL request/response schemas |
| MODIFY | `api/queue.py` | Add `doc_type` to published message |
| MODIFY | `api/routes/bills.py` | Add `doc_type` param to upload endpoint |
| NEW | `api/routes/bols.py` | New BOL CRUD routes |
| MODIFY | `api/main.py` | Register bols router |
| MODIFY | `worker/consumer.py` | Add BOL processing branch with validation |

### Frontend ([frontend/](file:///c:/Users/ALL%20USERS.DESKTOP-93DSICG/Geff/ocr_poc/frontend))

| Action | File | What changes |
|--------|------|-------------|
| MODIFY | `package.json` | Add `react-router-dom` |
| MODIFY | `src/main.jsx` | Wrap in `BrowserRouter` |
| MODIFY | `src/App.jsx` | Add routing, nav bar |
| MODIFY | `src/api/client.js` | Add BOL API functions |
| MODIFY | `src/components/UploadCard.jsx` | Add doc_type toggle, post-upload redirect |
| NEW | `src/components/BolHistoryPage.jsx` | BOL history/list view |
| NEW | `src/components/BolReviewPage.jsx` | BOL review/edit page |
| MODIFY | `src/components/BentoGrid.jsx` | Update stats for BOLs |

---

## Verification Plan

### Automated Tests
- Run the FastAPI server and verify all new endpoints return correct response shapes:
  ```bash
  # Test BOL CRUD
  curl http://localhost:8000/api/bols
  curl http://localhost:8000/api/bols/1
  ```
- Verify the migration SQL runs cleanly against the existing database
- Frontend build succeeds: `npm run build`

### Manual Verification
1. Upload a BOL image with `doc_type=bol` → verify consumer processes it → verify data appears in `bols`/`bol_containers` tables
2. Navigate to BOL History page → verify list shows the processed BOL
3. Click into BOL Review page → verify all 12 BOL fields + container rows are displayed
4. Edit fields and save → verify changes persist in the database
5. Verify existing invoice upload flow still works unchanged
6. Test with multi-container BOL (sample image 4) → verify both containers appear
