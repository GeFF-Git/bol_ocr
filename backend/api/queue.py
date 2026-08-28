import json, logging, os, pika
from dotenv import load_dotenv

load_dotenv()
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME   = "bill_processing_queue"
logger = logging.getLogger(__name__)

def publish_bill_message(bill_id: int, file_path: str, file_type: str, llm_engine: str) -> None:
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        payload = json.dumps({"bill_id": bill_id, "file_path": file_path, "file_type": file_type, "llm_engine": llm_engine})
        channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=payload, properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent))
    finally:
        connection.close()
