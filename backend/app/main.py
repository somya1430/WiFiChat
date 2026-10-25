from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Wi-Fi Chat API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/rooms", response_model=list[schemas.RoomRead])
def list_rooms(db: Session = Depends(get_db)):
    return db.scalars(select(models.Room).order_by(models.Room.name)).all()


@app.post("/api/rooms", response_model=schemas.RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(payload: schemas.RoomCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Room name cannot be blank")

    if db.scalar(select(models.Room).where(models.Room.name == name)):
        raise HTTPException(status_code=409, detail="A room with this name already exists")

    room = models.Room(name=name)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@app.get("/api/rooms/{room_id}/messages", response_model=list[schemas.MessageRead])
def list_messages(room_id: int, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    messages = db.scalars(
        select(models.Message)
        .where(models.Message.room_id == room_id)
        .order_by(models.Message.created_at.desc())
        .limit(100)
    ).all()
    return [
        schemas.MessageRead(
            id=message.id,
            room_id=message.room_id,
            author_name=message.author.username,
            body=message.body,
            created_at=message.created_at,
        )
        for message in reversed(messages)
    ]


@app.post(
    "/api/rooms/{room_id}/messages",
    response_model=schemas.MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(room_id: int, payload: schemas.MessageCreate, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    author_name = payload.author_name.strip()
    body = payload.body.strip()
    if not author_name or not body:
        raise HTTPException(status_code=422, detail="Message fields cannot be blank")

    user = db.scalar(select(models.User).where(models.User.username == author_name))
    if user is None:
        # Temporary identity handling for Stage 1. Stage 2 will replace this with JWT auth.
        user = models.User(username=author_name, password_hash="pending-auth")
        db.add(user)
        db.flush()

    message = models.Message(room_id=room.id, author_id=user.id, body=body)
    db.add(message)
    db.commit()
    db.refresh(message)

    return schemas.MessageRead(
        id=message.id,
        room_id=message.room_id,
        author_name=user.username,
        body=message.body,
        created_at=message.created_at,
    )
