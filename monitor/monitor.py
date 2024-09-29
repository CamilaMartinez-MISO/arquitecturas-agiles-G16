import logging
import os
import threading
import time

import pika

from health_check.health_check import HealthCheckReceiver

# Configuration constants
ALERT_API_URL = os.getenv("ALERT_API_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))
RETRY_INTERVAL = 5
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("monitor")


def connect_to_rabbitmq():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange="health_request_fanout", exchange_type="fanout")
            logger.info("Connected to RabbitMQ successfully")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ connection error: {e}, retrying in {RETRY_INTERVAL} seconds...")
            time.sleep(RETRY_INTERVAL)


def check_service_health(channel, health_request_id: int):
    message = json.dumps({"health_request_id": health_request_id})
    channel.basic_publish(
        exchange="health_request_fanout",
        routing_key="",
        body=message
    )
    logger.info(f"Sent health check request: {message}")


if __name__ == "__main__":
    threading.Thread(target=HealthCheckReceiver.init, daemon=True).start()
    connection, channel = connect_to_rabbitmq()
    health_request_id = 1
    try:
        while True:
            check_service_health(channel, health_request_id)
            health_request_id += 1
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Monitor shutting down.")
    finally:
        connection.close()
        logger.info("Closed RabbitMQ connection")
