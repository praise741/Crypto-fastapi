from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/market")
async def market_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(
                {
                    "type": "price_update",
                    "symbol": "BTC",
                    "data": {
                        "price": 20000.0,
                        "change_24h": 2.5,
                        "volume_24h": 1_000_000,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


@router.websocket("/predictions")
async def predictions_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(
                {
                    "type": "prediction_update",
                    "symbol": "BTC",
                    "data": {
                        "horizon": "24h",
                        "predicted_price": 21000.0,
                        "confidence": 0.65,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
