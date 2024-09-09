import logging
import os
import threading
import time
from datetime import datetime

import pika

RABBIT_RETRY_INTERVAL = int(os.environ.get("RABBIT_RETRY_INTERVAL", 5))
CHECK_OFFLINE_INTERVAL = int(os.environ.get("CHECK_OFFLINE_INTERVAL", 60))

lgr = logging.getLogger("health_check")
lgr.setLevel(logging.INFO)  # log all escalated at and above DEBUG
# add a file handler
fh = logging.FileHandler("health_check_log.csv")
fh.setLevel(logging.INFO)  # ensure all messages are logged to file

# create a formatter and set the formatter for the handler.
frmt = logging.Formatter("'%(asctime)s','%(name)s','%(levelname)s','%(message)s'")
fh.setFormatter(frmt)

# add the Handler to the logger
lgr.addHandler(fh)


class HealthCheckReceiver:
    last_response_times = {}

    @staticmethod
    def connect_to_rabbitmq():
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host="rabbitmq")
                )
                print("Connected to RabbitMQ successfully")
                return connection
            except pika.exceptions.AMQPConnectionError:
                print("RabbitMQ not ready, retrying in 5 seconds...")
                time.sleep(RABBIT_RETRY_INTERVAL)

    @staticmethod
    def init_response_channel(connection):
        channel = connection.channel()
        channel.queue_declare(queue="health_response_queue", durable=True)
        channel.basic_qos(prefetch_count=1)
        return channel

    @staticmethod
    def start_receiving_responses(connection, channel):
        channel.queue_declare(queue="health_response_queue", durable=True)

        def callback(ch, method, properties, body):
            app_id = properties.app_id
            HealthCheckReceiver.last_response_times[app_id] = datetime.now()
            message = f"{body}".replace("b'", "").replace("'", "")
            if '"status":"ok"' in message:
                lgr.info(f"{message}")
            else:
                lgr.error(f"{message}")

        channel.basic_consume(
            queue="health_response_queue", on_message_callback=callback, auto_ack=True
        )

        logging.info("Waiting for health check responses.")

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
        finally:
            connection.close()
        channel.start_consuming()

    @staticmethod
    def init():
        connection = HealthCheckReceiver.connect_to_rabbitmq()
        normal_channel = HealthCheckReceiver.init_response_channel(connection)

        def check_response_times():
            while True:
                current_time = datetime.now()
                for (
                    app_id,
                    response_time,
                ) in HealthCheckReceiver.last_response_times.items():
                    if not response_time:
                        continue
                    time_difference = current_time - response_time
                    if (
                        time_difference.total_seconds() >= CHECK_OFFLINE_INTERVAL
                        and time_difference.total_seconds()
                        < (CHECK_OFFLINE_INTERVAL * 2)
                    ):
                        lgr.warning(
                            f"Response time for {app_id} has exceeded {CHECK_OFFLINE_INTERVAL} seconds."
                        )
                    elif time_difference.total_seconds() > (CHECK_OFFLINE_INTERVAL * 2):
                        lgr.critical(
                            f"Response time for {app_id} has been offline for {time_difference.total_seconds()} seconds."
                        )
                time.sleep(CHECK_OFFLINE_INTERVAL)

        timer_thread = threading.Thread(target=check_response_times)
        timer_thread.start()
        HealthCheckReceiver.start_receiving_responses(connection, normal_channel)
