import logging
import os
import time
from datetime import datetime

import requests

SERVICE_URLS = os.getenv("SERVICE_URLS", []).split(",")
ALERT_API_URL = os.getenv("ALERT_API_URL", None)
CHECK_INTERVAL = os.getenv("CHECK_INTERVAL", 10)  # Interval in seconds

logging.basicConfig(filename="health_check.log", level=logging.INFO)


def send_alert(message):
    if ALERT_API_URL:
        requests.post(ALERT_API_URL, json={"text": message})


def check_service_health(service_url):
    try:
        response = requests.get(service_url)
        if response.status_code == 200:
            logging.info(f"{datetime.now()}: {service_url} is healthy")
        else:
            logging.error(
                f"{datetime.now()}: {service_url} unhealthy, status code: {response.status_code}"
            )
            send_alert(f"{service_url} unhealthy: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"{datetime.now()}: {service_url} unreachable, error: {e}")
        send_alert(f"{service_url} unreachable: {e}")


if __name__ == "__main__":
    while True:
        for service_url in SERVICE_URLS:
            check_service_health(service_url.strip())
        check_service_health()
        time.sleep(CHECK_INTERVAL)
