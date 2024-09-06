import logging
import os
import time
from datetime import datetime

import requests

SERVICE_URL = os.getenv("SERVICE_URL", None)
ALERT_API_URL = os.getenv("ALERT_API_URL", None)
CHECK_INTERVAL = os.getenv("CHECK_INTERVAL", 10)  # Interval in seconds

logging.basicConfig(filename="health_check.log", level=logging.INFO)


def send_alert(message):
    if ALERT_API_URL:
        requests.post(ALERT_API_URL, json={"text": message})


def check_service_health():
    try:
        response = requests.get(SERVICE_URL)
        if response.status_code == 200:
            logging.info(f"{datetime.now()}: Service is healthy")
        else:
            logging.error(
                f"{datetime.now()}: Service unhealthy, status code: {response.status_code}"
            )
            send_alert(f"Service unhealthy: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"{datetime.now()}: Service unreachable, error: {e}")
        send_alert(f"Service unreachable: {e}")


if __name__ == "__main__":
    while True:
        check_service_health()
        time.sleep(CHECK_INTERVAL)
