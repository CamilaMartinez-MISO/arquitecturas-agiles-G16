import logging
import os
import time
from datetime import datetime

import pika
import requests

SERVICE_URLS = os.getenv("SERVICE_URLS", []).split(",")
ALERT_API_URL = os.getenv("ALERT_API_URL", None)
CHECK_INTERVAL = os.getenv("CHECK_INTERVAL", 10)  # Interval in seconds

logging.basicConfig(filename="health_check.log", level=logging.INFO)

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

channel.queue_declare(queue="health_check_queue", durable=True)


def send_alert(message):
    if ALERT_API_URL:
        requests.post(ALERT_API_URL, json={"text": message})


def log_message(message, log_fn=logging.info, send_alert=False):
    log_fn(message)
    channel.basic_publish(exchange="", routing_key="health_check_queue", body=message)
    if send_alert:
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
                send_alert=True,
            )
    except requests.exceptions.RequestException as e:
        log_message(
            f"{datetime.now()}: {service_url} unreachable, error: {e}",
            logging.error,
            send_alert=True,
        )


if __name__ == "__main__":
    while True:
        for service_url in SERVICE_URLS:
            check_service_health(service_url.strip())
        check_service_health()
        time.sleep(CHECK_INTERVAL)

connection.close()
