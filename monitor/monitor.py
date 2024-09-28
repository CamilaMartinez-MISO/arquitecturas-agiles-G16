import logging
import os
import threading
import time

import pika
from health_check.health_check import HealthCheckReceiver

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

ALERT_API_URL = os.getenv("ALERT_API_URL", None)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))  # Interval in seconds
RETRY_INTERVAL = 5  # Interval to retry RabbitMQ connection in seconds
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")


def connect_to_rabbitmq():
    while True:
        try:
            logging.info("Connecting to RabbitMQ...{}".format(RABBITMQ_USER))
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host="rabbitmq",
                    credentials=credentials,
                ),
            )
            channel = connection.channel()
            channel.exchange_declare(
                exchange="health_request_fanout", exchange_type="fanout"
            )
            logging.info("Connected to RabbitMQ successfully")
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            logging.error("RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(RETRY_INTERVAL)


connection, channel = connect_to_rabbitmq()


def check_service_health(health_request_id: int):
    key = '"health_request_id"'
    channel.basic_publish(
        exchange="health_request_fanout",
        routing_key="",
        body=f"{{{key}: {health_request_id}}}",
    )


if __name__ == "__main__":
    rabbitmq_thread = threading.Thread(target=HealthCheckReceiver.init, daemon=True)
    rabbitmq_thread.start()
    health_request_id: int = 1
    while True:
        check_service_health(health_request_id)
        health_request_id = health_request_id + 1
        time.sleep(CHECK_INTERVAL)

connection.close()
