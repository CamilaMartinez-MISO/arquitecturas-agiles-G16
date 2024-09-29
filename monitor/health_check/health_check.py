import json
import logging
import os
import threading
import time
from datetime import datetime

import pika

# Configuration constants
RABBIT_RETRY_INTERVAL = int(os.getenv("RABBIT_RETRY_INTERVAL", 5))
CHECK_OFFLINE_INTERVAL = int(os.getenv("CHECK_OFFLINE_INTERVAL", 12))
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="'%(asctime)s','%(name)s','%(levelname)s','%(message)s'",
    handlers=[
        logging.FileHandler("health_check_log.csv"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("health_check")


class HealthCheckReceiver:
    last_response_times = {}

    @staticmethod
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
                logger.info("Connected to RabbitMQ successfully")
                return connection
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"RabbitMQ connection error: {e}, retrying in {RABBIT_RETRY_INTERVAL} seconds...")
                time.sleep(RABBIT_RETRY_INTERVAL)

    @staticmethod
    def init_response_channel(connection):
        channel = connection.channel()
        channel.queue_declare(queue="health_response_queue", durable=True)
        channel.basic_qos(prefetch_count=1)
        return channel

    @staticmethod
    def start_receiving_responses(channel):
        def callback(ch, method, properties, body):
            app_id = properties.app_id
            HealthCheckReceiver.last_response_times[app_id] = datetime.now()
            message = body.decode()
            try:
                data = json.loads(message)
                status = data.get("status")
                if status == "ok":
                    logger.info(f"Received health check OK from {app_id}: {message}")
                else:
                    logger.error(f"Received health check ERROR from {app_id}: {message}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")

        channel.basic_consume(
            queue="health_response_queue", on_message_callback=callback, auto_ack=True
        )

        logger.info("Waiting for health check responses.")

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error in consuming messages: {e}")

    @staticmethod
    def check_response_times():
        while True:
            current_time = datetime.now()
            for app_id, response_time in HealthCheckReceiver.last_response_times.items():
                if not response_time:
                    continue
                time_difference = (current_time - response_time).total_seconds()
                if CHECK_OFFLINE_INTERVAL <= time_difference < (CHECK_OFFLINE_INTERVAL * 2):
                    logger.warning(
                        f"Response time for {app_id} has exceeded {CHECK_OFFLINE_INTERVAL} seconds."
                    )
                elif time_difference >= (CHECK_OFFLINE_INTERVAL * 2):
                    logger.critical(
                        f"{app_id} has been offline for {time_difference} seconds."
                    )
            time.sleep(CHECK_OFFLINE_INTERVAL)

    @staticmethod
    def init():
        connection = HealthCheckReceiver.connect_to_rabbitmq()
        channel = HealthCheckReceiver.init_response_channel(connection)

        threading.Thread(target=HealthCheckReceiver.check_response_times, daemon=True).start()
        HealthCheckReceiver.start_receiving_responses(channel)


if __name__ == "__main__":
    HealthCheckReceiver.init()
