from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
import json
from fastapi import WebSocket, APIRouter, WebSocketDisconnect

configure_logging()

APP_ENV = config.APP_ENV
SHOW_DOCS_ENVIRONMENT = ("development", "staging")
app_configs = {"title": config.APP_NAME}
if APP_ENV not in SHOW_DOCS_ENVIRONMENT:
    app_configs["openapi_url"] = None

app_configs['openapi_url'] = "/operator-service/openapi.json"
app_configs['docs_url'] = "/operator-service/docs"

app = FastAPI(**app_configs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():

@app.on_event("shutdown")
async def shutdown():


@app.get("/operator-service/health")
async def health():
    return {"status": "ok"}

from app.websocket.websocket_manager import websocket_manager
@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: UUID):
    await websocket_manager.add_user_to_room(room_id, websocket)
    message = {
        "user_id": str(user_id),
        "room_id": room_id,
        "message": f"User {user_id} connected to room - {room_id}"
    }
    await websocket_manager.broadcast_to_room(room_id, json.dumps(message))
    try:
        while True:
            data = await websocket.receive_text()
            message = {
                "user_id": str(user_id),
                "room_id": room_id,
                "message": data
            }
            await websocket_manager.broadcast_to_room(room_id, json.dumps(message))

    except WebSocketDisconnect:
        await websocket_manager.remove_user_from_room(room_id, websocket)

        message = {
            "user_id": str(user_id),
            "room_id": room_id,
            "message": f"User {user_id} disconnected from room - {room_id}"
        }
        await websocket_manager.broadcast_to_room(room_id, json.dumps(message))



