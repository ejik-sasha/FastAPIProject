import pika
import json

def send_notification(event_type, data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='notifications', exchange_type='fanout')

    message = json.dumps({"event_type": event_type, "data": data})
    channel.basic_publish(exchange='notifications', routing_key='', body=message)

    connection.close()