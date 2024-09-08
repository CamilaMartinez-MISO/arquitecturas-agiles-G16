import logging
import os
import time
import random
from datetime import datetime

import pika
import requests

SERVICE_URLS = os.getenv("SERVICE_URLS", "").split(",")
ALERT_API_URL = os.getenv("ALERT_API_URL", None)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))  # Interval in seconds
RETRY_INTERVAL = 5  # Interval to retry RabbitMQ connection in seconds

logging.basicConfig(filename="health_check.log", level=logging.INFO)

def connect_to_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
            channel = connection.channel()
            channel.queue_declare(queue="health_check_queue", durable=True)
            logging.info("Connected to RabbitMQ successfully")
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            logging.error("RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(RETRY_INTERVAL)

connection, channel = connect_to_rabbitmq()

def send_alert(message):
    if ALERT_API_URL:
        requests.post(ALERT_API_URL, json={"text": message})


def log_message(message, log_fn=logging.info, alert_needed=False):
    log_fn(message)
    channel.basic_publish(exchange="", routing_key="health_check_queue", body=message)
    if alert_needed:
        send_alert(message)


def check_service_health(service_url):
    try:
        response = requests.get(service_url)
        if response.status_code == 200:
            log_message(f"{datetime.now()}: {service_url} is healthy")
        else:
            log_message(
                f"{datetime.now()}: {service_url} unhealthy, status code: {response.status_code}",
                logging.error,
                alert_needed=True,
            )
    except requests.exceptions.RequestException as e:
        log_message(
            f"{datetime.now()}: {service_url} unreachable, error: {e}",
            logging.error,
            alert_needed=True,
        )


if __name__ == "__main__":
    while True:
        for service_url in SERVICE_URLS:
            check_service_health(service_url.strip())
        time.sleep(CHECK_INTERVAL)

connection.close()
