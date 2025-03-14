import pika
import json
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
import threading

def callback(ch, method, properties, body):
    message = json.loads(body)
    event_type = message.get("event_type")
    data = message.get("data")

    if event_type == "new_post":
        print(f"New post notification: {data}")
    elif event_type == "like":
        print(f"Like notification: {data}")
    elif event_type == "retweet":
        print(f"Retweet notification: {data}")

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='notifications', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='notifications', queue=queue_name)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for notifications. To exit press CTRL+C')
    channel.start_consuming()

@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    yield

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)