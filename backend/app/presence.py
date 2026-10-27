from collections import defaultdict

from fastapi import WebSocket


class PresenceManager:
    """In-memory room presence for a single FastAPI process."""

    def __init__(self):
        self.connections: dict[int, dict[int, set[WebSocket]]] = defaultdict(lambda: defaultdict(set))
        self.usernames: dict[int, dict[int, str]] = defaultdict(dict)

    async def connect(self, room_id: int, user_id: int, username: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[room_id][user_id].add(websocket)
        self.usernames[room_id][user_id] = username

    def disconnect(self, room_id: int, user_id: int, websocket: WebSocket):
        room_connections = self.connections.get(room_id, {})
        user_connections = room_connections.get(user_id, set())
        user_connections.discard(websocket)
        if not user_connections:
            room_connections.pop(user_id, None)
            self.usernames.get(room_id, {}).pop(user_id, None)
        if not room_connections:
            self.connections.pop(room_id, None)
            self.usernames.pop(room_id, None)

    def participants(self, room_id: int) -> list[dict[str, object]]:
        return [
            {"id": user_id, "username": username}
            for user_id, username in self.usernames.get(room_id, {}).items()
        ]

    async def broadcast(self, room_id: int, event: dict[str, object]):
        recipients = [
            websocket
            for sockets in self.connections.get(room_id, {}).values()
            for websocket in sockets
        ]
        for websocket in recipients:
            try:
                await websocket.send_json(event)
            except RuntimeError:
                pass


presence_manager = PresenceManager()
