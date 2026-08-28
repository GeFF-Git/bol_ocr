import json, logging, os, sys, tempfile, fitz, pika, psycopg2
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
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    pix.save(tmp.name)
    tmp.close()
    doc.close()
    return tmp.name

def process_bill(bill_id, file_path, file_type, llm_engine):
    conn = get_conn()
    tmp_img = None
    try:
        abs_file_path = (BASE_DIR / file_path).resolve() if not Path(file_path).is_absolute() else Path(file_path)
        abs_file_path = str(abs_file_path)
        img_path = pdf_to_image(abs_file_path) if file_type == "pdf" else abs_file_path
        tmp_img = img_path if file_type == "pdf" else None

        from extractors.factory import get_extractor
        extractor = get_extractor(llm_engine)
        data = extractor.extract(img_path)

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
        logging.info(f"✅ Bill #{bill_id} processed via {llm_engine}")
    except Exception as e:
        logging.error(f"❌ Bill #{bill_id} error: {e}")
        with conn.cursor() as cur:
            cur.execute("UPDATE bills SET status='FAILED', error_message=%s WHERE id=%s", (str(e)[:1000], bill_id))
        conn.commit()
    finally:
        if tmp_img and os.path.exists(tmp_img): os.remove(tmp_img)
        conn.close()

def callback(ch, method, props, body):
    payload = json.loads(body)
    process_bill(payload["bill_id"], payload["file_path"], payload["file_type"], payload["llm_engine"])
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    logging.info("🚀 Worker ready. Consuming RabbitMQ...")
    ch.start_consuming()

if __name__ == "__main__": main()
