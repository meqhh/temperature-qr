"""
Server WebSocket + HTTP sederhana untuk monitoring suhu & kelembapan DHT11.

Alur:
- ESP32 terhubung sebagai WebSocket client, kirim {"type": "hello", "role": "device"}
  lalu berkala kirim {"type": "data", "suhu": ..., "kelembapan": ...}
- Browser (frontend) terhubung sebagai WebSocket client, kirim
  {"type": "hello", "role": "frontend"} lalu menerima broadcast update.

Jalankan dengan:
    pip install -r requirements.txt
    python server.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from aiohttp import web, WSMsgType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("server")

BASE_DIR = Path(__file__).parent
INDEX_FILE = BASE_DIR / "static" / "index.html"

frontend_clients: set[web.WebSocketResponse] = set()

latest_data: dict[str, str | float | None] = {
    "suhu": None,
    "kelembapan": None,
    "timestamp": None,
}

async def index_handler(request: web.Request) -> web.FileResponse:
    return web.FileResponse(INDEX_FILE)


async def broadcast_to_frontend(payload: dict) -> None:
    disconnected = set()
    for client in frontend_clients:
        if client.closed:
            disconnected.add(client)
            continue
        try:
            await client.send_json(payload)
        except ConnectionResetError:
            disconnected.add(client)
    frontend_clients.difference_update(disconnected)


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    role = None
    logger.info("Client baru terhubung dari %s", request.remote)

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                if msg.type == WSMsgType.ERROR:
                    logger.error("WebSocket error: %s", ws.exception())
                continue

            try:
                data = json.loads(msg.data)
            except json.JSONDecodeError:
                logger.warning("Pesan bukan JSON valid, diabaikan: %s", msg.data)
                continue

            msg_type = data.get("type")

            if msg_type == "hello":
                role = data.get("role")
                logger.info("Client mendaftar sebagai role='%s'", role)

                if role == "frontend":
                    frontend_clients.add(ws)
                    if latest_data["timestamp"] is not None:
                        await ws.send_json({"type": "update", **latest_data})

            elif msg_type == "data" and role == "device":
                suhu = data.get("suhu")
                kelembapan = data.get("kelembapan")
                time = datetime.now().isoformat(timespec="seconds")

                latest_data["suhu"] = suhu
                latest_data["kelembapan"] = kelembapan
                latest_data["timestamp"] = time

                logger.info("Data diterima dari device: suhu=%s°C, kelembapan=%s%%", suhu, kelembapan)

                await broadcast_to_frontend({"type": "update", **latest_data})

            else:
                logger.warning("Pesan tidak dikenali (type=%s, role=%s)", msg_type, role)

    finally:
        frontend_clients.discard(ws)
        logger.info("Client terputus (role=%s)", role)

    return ws


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_static("/static/", path=BASE_DIR / "static", name="static")
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)
