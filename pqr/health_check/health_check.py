import json
import os
import time

import pika

RETRY_INTERVAL = 5  # Intervalo para reintentar conexión a RabbitMQ en segundos
INSTANCE_ID = os.getenv("INSTANCE_ID")


class HealthCheck:
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
    def init_fanout_channel(connection):
        channel = connection.channel()
        channel.exchange_declare(
            exchange="health_request_fanout", exchange_type="fanout"
        )
        channel.basic_qos(prefetch_count=1)

        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange="health_request_fanout", queue=queue_name)

        def callback(ch, method, properties, body):
            print(f"Data receive: {body.decode()}")
            try:
                data = json.loads(body.decode())
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON: {e}")
                data = {}

            health_request_id = data.get("health_request_id", None)

            channel.basic_publish(
                exchange="",
                routing_key="health_response_queue",
                properties=pika.BasicProperties(app_id=f"pqr_{INSTANCE_ID}"),
                body=f'instance_id: {INSTANCE_ID}, health_request_id: {health_request_id}, "status":"ok"',
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(
            queue=queue_name, on_message_callback=callback, auto_ack=False
        )
        return channel

    @staticmethod
    def init():
        connection = HealthCheck.connect_to_rabbitmq()
        fanout_channel = HealthCheck.init_fanout_channel(connection)

        print("Waiting for messages...")
        try:
            fanout_channel.start_consuming()
        except KeyboardInterrupt:
            fanout_channel.stop_consuming()
        finally:
            connection.close()
