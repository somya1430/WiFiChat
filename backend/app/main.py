from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, SessionLocal, engine, get_db
from .presence import presence_manager
from .security import (
    create_access_token,
    get_current_user,
    hash_password,
    user_id_from_token,
    verify_password,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Wi-Fi Chat API", version="0.2.0", lifespan=lifespan)

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


@app.post("/api/auth/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.Credentials, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=422, detail="Username must have at least 3 characters")
    if db.scalar(select(models.User).where(models.User.username == username)):
        raise HTTPException(status_code=409, detail="That username is already taken")

    user = models.User(username=username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.TokenResponse(access_token=create_access_token(user), user=user)


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.username == payload.username.strip()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return schemas.TokenResponse(access_token=create_access_token(user), user=user)


@app.get("/api/auth/me", response_model=schemas.UserRead)
def current_user(user: models.User = Depends(get_current_user)):
    return user


@app.get("/api/rooms", response_model=list[schemas.RoomRead])
def list_rooms(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(models.Room).order_by(models.Room.name)).all()


@app.post("/api/rooms", response_model=schemas.RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: schemas.RoomCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Room name cannot be blank")

    if db.scalar(select(models.Room).where(models.Room.name == name)):
        raise HTTPException(status_code=409, detail="A room with this name already exists")

    room = models.Room(name=name)
    db.add(room)
    db.flush()
    db.add(models.RoomMember(room_id=room.id, user_id=user.id))
    db.commit()
    db.refresh(room)
    return room


def get_membership(room_id: int, user_id: int, db: Session) -> models.RoomMember:
    membership = db.scalar(
        select(models.RoomMember).where(
            models.RoomMember.room_id == room_id,
            models.RoomMember.user_id == user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Join this room before viewing its messages")
    return membership


@app.post("/api/rooms/{room_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def join_room(
    room_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(models.Room, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")
    membership = db.scalar(
        select(models.RoomMember).where(
            models.RoomMember.room_id == room_id,
            models.RoomMember.user_id == user.id,
        )
    )
    if membership is None:
        db.add(models.RoomMember(room_id=room_id, user_id=user.id))
        db.commit()


@app.get("/api/rooms/{room_id}/messages", response_model=list[schemas.MessageRead])
def list_messages(
    room_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(models.Room, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")
    get_membership(room_id, user.id, db)
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
def create_message(
    room_id: int,
    payload: schemas.MessageCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(models.Room, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message cannot be blank")
    get_membership(room_id, user.id, db)

    message = models.Message(room_id=room_id, author_id=user.id, body=body)
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


@app.websocket("/api/ws/rooms/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: int):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = user_id_from_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db = SessionLocal()
    try:
        user = db.get(models.User, user_id)
        room = db.get(models.Room, room_id)
        membership = db.scalar(
            select(models.RoomMember).where(
                models.RoomMember.room_id == room_id,
                models.RoomMember.user_id == user_id,
            )
        )
        if user is None or room is None or membership is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        username = user.username
    finally:
        db.close()

    await presence_manager.connect(room_id, user_id, username, websocket)
    await presence_manager.broadcast(
        room_id, {"type": "participants", "participants": presence_manager.participants(room_id)}
    )

    try:
        while True:
            event = await websocket.receive_json()
            if event.get("type") != "message" or not isinstance(event.get("body"), str):
                continue
            body = event["body"].strip()
            if not body or len(body) > 2000:
                continue

            db = SessionLocal()
            try:
                message = models.Message(room_id=room_id, author_id=user_id, body=body)
                db.add(message)
                db.commit()
                db.refresh(message)
                payload = schemas.MessageRead(
                    id=message.id,
                    room_id=message.room_id,
                    author_name=username,
                    body=message.body,
                    created_at=message.created_at,
                ).model_dump(mode="json")
            finally:
                db.close()
            await presence_manager.broadcast(room_id, {"type": "message", "message": payload})
    except WebSocketDisconnect:
        pass
    finally:
        presence_manager.disconnect(room_id, user_id, websocket)
        await presence_manager.broadcast(
            room_id, {"type": "participants", "participants": presence_manager.participants(room_id)}
        )
