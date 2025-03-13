import pika
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Notification(BaseModel):
    user_id: int
    message: str

notifications_db = []

def callback(ch, method, properties, body):
    data = json.loads(body)
    notification = Notification(user_id=data['user_id'], message=data['message'])
    notifications_db.append(notification)
    print(f"Received notification: {notification}")

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='notifications')
    channel.basic_consume(queue='notifications', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

@app.on_event("startup")
def startup_event():
    import threading
    threading.Thread(target=start_consumer, daemon=True).start()

@app.get("/notifications/", response_model=List[Notification])
def get_notifications():
    return notifications_db

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)