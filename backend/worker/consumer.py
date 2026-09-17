import json, logging, os, sys, tempfile, time, pymupdf, pika, psycopg2
from datetime import date
from pathlib import Path
from psycopg2.extras import Json
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "bill_processing_queue"

def get_conn():
    url = os.getenv("DATABASE_URL", "postgresql://postgres:Geoffrey2001@localhost:5432/bill_processor").replace("postgresql+asyncpg://", "postgresql://")
    return psycopg2.connect(url)

def pdf_to_image(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    pix.save(tmp.name)
    tmp.close()
    doc.close()
    return tmp.name

def validate_bol_data(data: dict) -> dict:
    """Validate and normalize BOL extraction data. Logs warnings for issues but doesn't raise."""
    # Ensure notify_parties is a list
    np = data.get("notify_parties")
    if np is None:
        data["notify_parties"] = []
    elif isinstance(np, str):
        logging.warning("notify_parties was a string, coercing to list")
        data["notify_parties"] = [np]
    elif not isinstance(np, list):
        logging.warning(f"notify_parties has unexpected type {type(np)}, defaulting to empty list")
        data["notify_parties"] = []

    # Ensure containers is a list
    containers = data.get("containers")
    if containers is None:
        logging.warning("No containers found in extraction output")
        data["containers"] = []
    elif isinstance(containers, dict):
        logging.warning("containers was a single object, coercing to list")
        data["containers"] = [containers]
    elif not isinstance(containers, list):
        logging.warning(f"containers has unexpected type {type(containers)}, defaulting to empty list")
        data["containers"] = []

    # Validate each container has expected keys
    expected_container_keys = {"container_number", "seal_number", "marks_and_numbers", "description", "gross_cargo_weight", "measurement"}
    for i, c in enumerate(data["containers"]):
        if not isinstance(c, dict):
            logging.warning(f"Container at index {i} is not a dict, skipping")
            continue
        missing = expected_container_keys - set(c.keys())
        if missing:
            logging.warning(f"Container at index {i} missing keys: {missing}")
            for key in missing:
                c[key] = None

    # Log missing BOL-level keys
    expected_bol_keys = {"bol_number", "shipper", "consignee", "notify_parties", "discharge_agent",
                         "vessel_voyage", "port_of_loading", "place_of_receipt", "booking_ref",
                         "port_of_discharge", "place_of_delivery", "shipped_on_board_date", "containers"}
    missing_bol = expected_bol_keys - set(data.keys())
    if missing_bol:
        logging.warning(f"BOL extraction missing top-level keys: {missing_bol}")
        for key in missing_bol:
            data[key] = None

    return data

def process_invoice(bill_id, data, conn):
    """Existing invoice processing logic."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE bills SET
                status='PROCESSED', vendor_name=%s, vendor_address=%s, invoice_number=%s,
                currency=%s, line_items=%s, subtotal=%s, tax_amount=%s, discount=%s,
                total_amount=%s, payment_method=%s, notes=%s, error_message=NULL, updated_at=NOW()
            WHERE id=%s
        """, (
            data.get("vendor_name"), data.get("vendor_address"), data.get("invoice_number"),
            data.get("currency"), Json(data.get("line_items") or []),
            data.get("subtotal"), data.get("tax_amount"), data.get("discount"),
            data.get("total_amount") or 0.0, data.get("payment_method"), data.get("notes"),
            bill_id
        ))
    conn.commit()

def process_bol(bill_id, data, conn):
    """New BOL processing logic — writes to bols + bol_containers tables."""
    data = validate_bol_data(data)

    with conn.cursor() as cur:
        # Insert BOL record
        cur.execute("""
            INSERT INTO bols (bill_id, bol_number, shipper, consignee, notify_parties,
                discharge_agent, vessel_voyage, port_of_loading, place_of_receipt,
                booking_ref, port_of_discharge, place_of_delivery, shipped_on_board_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            bill_id,
            data.get("bol_number"),
            data.get("shipper"),
            data.get("consignee"),
            Json(data.get("notify_parties") or []),
            data.get("discharge_agent"),
            data.get("vessel_voyage"),
            data.get("port_of_loading"),
            data.get("place_of_receipt"),
            data.get("booking_ref"),
            data.get("port_of_discharge"),
            data.get("place_of_delivery"),
            data.get("shipped_on_board_date")
        ))
        bol_id = cur.fetchone()[0]

        # Insert containers
        containers = [c for c in data.get("containers", []) if isinstance(c, dict)]
        for c in containers:
            cur.execute("""
                INSERT INTO bol_containers (bol_id, container_number, seal_number,
                    marks_and_numbers, description, gross_cargo_weight, measurement)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                bol_id,
                c.get("container_number"),
                c.get("seal_number"),
                c.get("marks_and_numbers"),
                c.get("description"),
                c.get("gross_cargo_weight"),
                c.get("measurement")
            ))

        # Update bills status
        cur.execute("UPDATE bills SET status='PROCESSED', error_message=NULL, updated_at=NOW() WHERE id=%s", (bill_id,))
    conn.commit()
    logging.info(f"  → Inserted BOL #{bol_id} with {len(containers)} container(s)")

def process_bill(bill_id, file_path, file_type, llm_engine, doc_type="invoice"):
    conn = None
    tmp_img = None
    try:
        conn = get_conn()
        abs_file_path = (BASE_DIR / file_path).resolve() if not Path(file_path).is_absolute() else Path(file_path)
        abs_file_path = str(abs_file_path)
        img_path = pdf_to_image(abs_file_path) if file_type == "pdf" else abs_file_path
        tmp_img = img_path if file_type == "pdf" else None

        from extractors.factory import get_extractor
        extractor = get_extractor(llm_engine)

        if doc_type == "bol":
            from prompts.extraction_prompt import BOL_EXTRACTION_PROMPT
            data = extractor.extract(img_path, prompt=BOL_EXTRACTION_PROMPT)
            process_bol(bill_id, data, conn)
        else:
            data = extractor.extract(img_path)
            process_invoice(bill_id, data, conn)

        logging.info(f"✅ Bill #{bill_id} processed via {llm_engine} (doc_type={doc_type})")
    except Exception as e:
        logging.error(f"❌ Bill #{bill_id} error: {e}")
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE bills SET status='FAILED', error_message=%s WHERE id=%s", (str(e)[:1000], bill_id))
                conn.commit()
            except Exception as db_err:
                logging.error(f"Failed to update bill #{bill_id} status in DB: {db_err}")
    finally:
        if tmp_img and os.path.exists(tmp_img):
            try:
                os.remove(tmp_img)
            except OSError:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def callback(ch, method, props, body):
    try:
        payload = json.loads(body)
        process_bill(
            payload["bill_id"],
            payload["file_path"],
            payload["file_type"],
            payload["llm_engine"],
            payload.get("doc_type", "invoice")
        )
    except Exception as exc:
        logging.error(f"Unexpected callback error: {exc}")
    finally:
        try:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as ack_err:
            logging.error(f"Failed to ack message: {ack_err}")

def run_consumer():
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 0  # Disable heartbeat to prevent socket timeout during long LLM inference
    params.blocked_connection_timeout = 3600
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    logging.info("🚀 Worker ready. Consuming RabbitMQ...")
    ch.start_consuming()

def main():
    while True:
        try:
            run_consumer()
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.StreamLostError) as e:
            logging.warning(f"RabbitMQ connection lost ({e}). Reconnecting in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            logging.info("Worker stopped by user.")
            break
        except Exception as e:
            logging.error(f"Worker encountered unexpected error: {e}. Retrying in 5 seconds...", exc_info=True)
            time.sleep(5)

if __name__ == "__main__": main()
