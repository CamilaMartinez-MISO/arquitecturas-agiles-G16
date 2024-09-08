import time

import pika

RETRY_INTERVAL = 5  # Interval to retry RabbitMQ connection in seconds


class HealthCheck:
    @staticmethod
    def connect_to_rabbitmq():
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host="rabbitmq")
                )
                channel = connection.channel()
                channel.queue_declare(queue="health_check_queue", durable=True)
                print("Connected to RabbitMQ successfully")
                return connection, channel
            except pika.exceptions.AMQPConnectionError:
                print("RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(RETRY_INTERVAL)

    @staticmethod
    def init():
        connection, channel = HealthCheck.connect_to_rabbitmq()

        print(" Waiting for messages...")

        def callback(ch, method, properties, body):
            print(" Received %s" % body.decode())
            print(" Done")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue="health_check_queue", on_message_callback=callback)
        channel.start_consuming()
