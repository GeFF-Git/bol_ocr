CREATE TABLE IF NOT EXISTS bols (
    id                    SERIAL PRIMARY KEY,
    bill_id               INTEGER REFERENCES bills(id) ON DELETE SET NULL,
    bol_number            TEXT,
    shipper               TEXT,
    consignee             TEXT,
    notify_parties        JSONB DEFAULT '[]'::jsonb,
    discharge_agent       TEXT,
    vessel_voyage         TEXT,
    port_of_loading       TEXT,
    place_of_receipt      TEXT,
    booking_ref           TEXT,
    port_of_discharge     TEXT,
    place_of_delivery     TEXT,
    shipped_on_board_date DATE,
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bol_containers (
    id                  SERIAL PRIMARY KEY,
    bol_id              INTEGER NOT NULL REFERENCES bols(id) ON DELETE CASCADE,
    container_number    TEXT,
    seal_number         TEXT,
    marks_and_numbers   TEXT,
    description         TEXT,
    gross_cargo_weight  TEXT,
    measurement         TEXT
);
