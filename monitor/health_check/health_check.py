import logging
import os
import time

import pika

RETRY_INTERVAL = 5  # Intervalo para reintentar conexión a RabbitMQ en segundos

SERVICES_TO_CHECK = os.getenv("SERVICES_TO_CHECK", "").split(",")


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
                time.sleep(RETRY_INTERVAL)

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

        HealthCheckReceiver.start_receiving_responses(connection, normal_channel)
