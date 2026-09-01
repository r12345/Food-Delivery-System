from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..security import decode_token

router = APIRouter()

# 商家在线连接：owner_user_id -> WebSocket
merchant_connections: dict[int, WebSocket] = {}


async def push_to_merchant(user_id: int, data: dict):
    ws = merchant_connections.get(user_id)
    if ws is None:
        return
    try:
        await ws.send_json(data)
    except Exception:
        merchant_connections.pop(user_id, None)


@router.websocket("/ws/merchant")
async def ws_merchant(websocket: WebSocket, token: str = ""):
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError
        user_id = int(payload["sub"])
        if payload.get("role") != "merchant":
            raise ValueError
    except Exception:
        await websocket.close(code=4001)
        return
    await websocket.accept()
    merchant_connections[user_id] = websocket
    try:
        while True:
            await websocket.receive_text()  # 心跳/保活
    except WebSocketDisconnect:
        merchant_connections.pop(user_id, None)
