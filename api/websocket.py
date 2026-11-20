"""WebSocket /ws/live pushing events."""
from __future__ import annotations

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    bus = get_event_bus()
    queue = bus.subscribe()  # all events

    # Heartbeat task
    async def heartbeat():
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_json({"type": "ping", "ts": "", "payload": {"message": "heartbeat"}})
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            try:
                # Wait for event with timeout to allow checking disconnect
                envelope = await asyncio.wait_for(queue.get(), timeout=60.0)
                await websocket.send_json(envelope)
            except asyncio.TimeoutError:
                # No events, continue loop, heartbeat will handle
                continue
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.warning(f"WebSocket send error: {e}")
                break
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass
        bus.unsubscribe(queue)
        try:
            await websocket.close()
        except Exception:
            pass
