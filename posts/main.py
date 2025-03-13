import pika
import json
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db

app = FastAPI()

def send_notification(user_id: int, message: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='notifications')
    channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps({'user_id': user_id, 'message': message}))
    connection.close()

@app.post("/", response_model=schemas.Post)
def create_new_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_post = models.Post(content=post.content, owner_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    send_notification(current_user.id, f"New post created: {post.content}")
    return db_post

@app.post("/{post_id}/like", status_code=204)
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail='Post not found')
    like = db.query(models.Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        raise HTTPException(status_code=400, detail="Already liked")
    new_like = models.Like(user_id=current_user.id, post_id=post_id)
    db.add(new_like)
    db.commit()
    send_notification(post.owner_id, f"Your post was liked by {current_user.username}")
    return

@app.post("/{post_id}/retweet", status_code=204)
def retweet_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail='Post not found')
    retweet = db.query(models.Retweet).filter_by(user_id=current_user.id, post_id=post_id).first()
    if retweet:
        raise HTTPException(status_code=400, detail="Already retweeted")
    new_retweet = models.Retweet(user_id=current_user.id, post_id=post_id)
    db.add(new_retweet)
    db.commit()
    send_notification(post.owner_id, f"Your post was retweeted by {current_user.username}")
    return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)