import json
import logging
import os
import random
import time

import pika

# Configuration constants
RETRY_INTERVAL = 5  # Interval to retry RabbitMQ connection in seconds
INSTANCE_ID = os.getenv("INSTANCE_ID", "1")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
IS_FAILING_SERVICE = os.getenv("IS_FAILING_SERVICE", "False").lower() == "true"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("health_check_pqr_log.csv"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("health_check")


class HealthCheck:
    @staticmethod
    def is_health_ok() -> bool:
        # Determine if the service should simulate failure
        if IS_FAILING_SERVICE:
            result = random.choice([True, False])
            logging.info(f"Service health check result (simulated failure mode): {result}")
            return result
        else:
            logging.info("Service health check result: True")
            return True

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
                logging.info("Connected to RabbitMQ successfully")
                return connection
            except pika.exceptions.AMQPConnectionError as e:
                logging.error(f"RabbitMQ connection error: {e}, retrying in {RETRY_INTERVAL} seconds...")
                time.sleep(RETRY_INTERVAL)

    @staticmethod
    def init_fanout_channel(connection):
        channel = connection.channel()
        channel.exchange_declare(exchange="health_request_fanout", exchange_type="fanout")
        channel.queue_declare(queue="health_response_queue", durable=True)

        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange="health_request_fanout", queue=queue_name)
        logging.info("Fanout channel and queue initialized successfully")

        def callback(ch, method, properties, body):
            logging.info(f"Received health check request: {body.decode()}")
            try:
                data = json.loads(body.decode())
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            health_request_id = data.get("health_request_id")
            status = "ok" if HealthCheck.is_health_ok() else "error"
            message = json.dumps({
                "instance_id": INSTANCE_ID,
                "health_request_id": health_request_id,
                "status": status
            })
            ch.basic_publish(
                exchange="",
                routing_key="health_response_queue",
                properties=pika.BasicProperties(app_id=f"pqr_{INSTANCE_ID}"),
                body=message
            )
            logging.info(f"Sent health check response: {message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        return channel

    @staticmethod
    def init():
        connection = HealthCheck.connect_to_rabbitmq()
        fanout_channel = HealthCheck.init_fanout_channel(connection)

        logging.info("Waiting for health check requests...")
        try:
            fanout_channel.start_consuming()
        except KeyboardInterrupt:
            fanout_channel.stop_consuming()
        finally:
            connection.close()
            logging.info("Closed RabbitMQ connection")


if __name__ == "__main__":
    HealthCheck.init()
