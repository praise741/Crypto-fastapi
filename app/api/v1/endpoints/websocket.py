from __future__ import annotations

import asyncio
from typing import Callable, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.market_data import get_latest_price
from app.services.prediction import get_predictions


router = APIRouter(prefix="/ws", tags=["WebSocket"])


class SubscriptionServer:
    def __init__(self, max_topics: int, fetcher: Callable[[str], Dict]):
        self.max_topics = max_topics
        self.fetcher = fetcher
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.subscriptions[websocket] = set()

    async def disconnect(self, websocket: WebSocket) -> None:
        self.subscriptions.pop(websocket, None)

    async def handle(self, websocket: WebSocket) -> None:
        await self.connect(websocket)
        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                except asyncio.TimeoutError:
                    await self._push_updates(websocket)
                    continue

                action = message.get("action")
                symbols = message.get("symbols") or []
                if action == "subscribe":
                    if len(symbols) > self.max_topics:
                        symbols = symbols[: self.max_topics]
                    self.subscriptions[websocket] = {symbol.upper() for symbol in symbols}
                    await websocket.send_json({"type": "subscribed", "symbols": list(self.subscriptions[websocket])})
                elif action == "unsubscribe":
                    for symbol in symbols:
                        self.subscriptions[websocket].discard(symbol.upper())
                    await websocket.send_json({"type": "unsubscribed", "symbols": list(symbols)})
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    async def _push_updates(self, websocket: WebSocket) -> None:
        symbols = self.subscriptions.get(websocket, set())
        if not symbols:
            return
        for symbol in list(symbols)[: self.max_topics]:
            payload = await asyncio.get_event_loop().run_in_executor(None, self.fetcher, symbol)
            if payload:
                await websocket.send_json(payload)


def _fetch_market_payload(symbol: str) -> Dict:
    with SessionLocal() as session:
        price = get_latest_price(session, symbol)
    return {
        "type": "price_update",
        "symbol": symbol.upper(),
        "data": price.model_dump(),
    }


def _fetch_prediction_payload(symbol: str) -> Dict:
    with SessionLocal() as session:
        response = get_predictions(session, symbol=symbol, horizons=["1h", "4h", "24h"])
    return {
        "type": "prediction_update",
        "symbol": symbol.upper(),
        "data": [item.model_dump() for item in response.predictions],
    }


market_server = SubscriptionServer(max_topics=5, fetcher=_fetch_market_payload)
prediction_server = SubscriptionServer(max_topics=3, fetcher=_fetch_prediction_payload)


@router.websocket("/market")
async def market_feed(websocket: WebSocket):
    if not settings.FEATURE_DASHBOARD:
        await websocket.close()
        return
    await market_server.handle(websocket)


@router.websocket("/predictions")
async def predictions_feed(websocket: WebSocket):
    if not settings.FEATURE_PREDICTIONS:
        await websocket.close()
        return
    await prediction_server.handle(websocket)
