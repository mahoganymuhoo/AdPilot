"""
WebSocket Real-time Dashboard

Endpoint: WS /ws/metrics/{seller_id}

Çalışma prensibi:
1. Client bağlandığında anlık snapshot gönderilir
2. Celery sync tamamladıktan sonra Redis pubsub üzerinden broadcast
3. Client disconnect durumunda temizlenir

Mesaj formatı:
{
  "type": "snapshot" | "update" | "anomaly_alert" | "ping",
  "seller_id": 1,
  "data": {...},
  "timestamp": "ISO8601"
}
"""
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.ad_metrics import AdMetric
from app.models.product import Product
from app.models.seller import Seller

router = APIRouter(tags=["websocket"])

# Aktif bağlantıları tut: seller_id → WebSocket set
_connections: dict[int, set[WebSocket]] = {}


class ConnectionManager:
    def add(self, seller_id: int, ws: WebSocket):
        _connections.setdefault(seller_id, set()).add(ws)

    def remove(self, seller_id: int, ws: WebSocket):
        if seller_id in _connections:
            _connections[seller_id].discard(ws)
            if not _connections[seller_id]:
                del _connections[seller_id]

    async def send(self, seller_id: int, message: dict):
        """Bir seller'ın tüm aktif bağlantılarına mesaj gönder."""
        dead = set()
        for ws in _connections.get(seller_id, set()):
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.remove(seller_id, ws)

    async def broadcast(self, message: dict):
        """Tüm bağlı client'lara gönder."""
        for seller_id in list(_connections.keys()):
            await self.send(seller_id, message)

    def connection_count(self) -> int:
        return sum(len(v) for v in _connections.values())


manager = ConnectionManager()


async def _build_snapshot(seller_id: int, db: AsyncSession) -> dict:
    """Anlık dashboard verisini DB'den çek."""
    since = datetime.now(timezone.utc) - timedelta(days=1)

    q = await db.execute(
        select(
            func.sum(AdMetric.revenue).label("revenue"),
            func.sum(AdMetric.ad_spend).label("spend"),
            func.sum(AdMetric.conversions).label("conversions"),
            func.sum(AdMetric.clicks).label("clicks"),
            func.count(AdMetric.id).label("records"),
        )
        .join(Product, Product.id == AdMetric.product_id)
        .where(Product.seller_id == seller_id, AdMetric.time >= since)
    )
    row = q.one_or_none()

    revenue = float(row.revenue or 0)
    spend = float(row.spend or 0)
    conversions = int(row.conversions or 0)
    clicks = int(row.clicks or 0)

    return {
        "type": "snapshot",
        "seller_id": seller_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "last_24h": {
                "revenue": round(revenue, 2),
                "ad_spend": round(spend, 2),
                "roas": round(revenue / spend, 3) if spend > 0 else 0,
                "conversions": conversions,
                "clicks": clicks,
                "records": int(row.records or 0),
            }
        },
    }


@router.websocket("/ws/metrics/{seller_id}")
async def metrics_ws(
    websocket: WebSocket,
    seller_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Real-time metrik stream.
    Bağlanıldığında anlık snapshot gönderilir, sonra 60 saniyede bir ping.
    Celery task'lar yeni veri geldiğinde `notify_seller()` ile push yapar.
    """
    await websocket.accept()
    manager.add(seller_id, websocket)

    try:
        # İlk anlık snapshot
        snapshot = await _build_snapshot(seller_id, db)
        await websocket.send_text(json.dumps(snapshot, default=str))

        # Ping döngüsü — bağlantıyı canlı tut
        while True:
            try:
                # Client'tan mesaj bekliyoruz (ping/pong veya disconnect)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=55.0)
                msg = json.loads(data) if data else {}
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }))
                elif msg.get("type") == "refresh":
                    # Client manuel yenileme istedi
                    snapshot = await _build_snapshot(seller_id, db)
                    await websocket.send_text(json.dumps(snapshot, default=str))

            except asyncio.TimeoutError:
                # 55 saniye geçti — sunucu tarafından ping gönder
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "connections": manager.connection_count(),
                }))

    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(seller_id, websocket)


async def notify_seller(seller_id: int, event_type: str, data: dict):
    """
    Celery task'lardan çağrılır — yeni veri veya anomali bildirimi gönderir.

    Kullanım (celery task içinden):
        from app.api.ws import notify_seller
        await notify_seller(seller_id=1, event_type="update", data={...})
    """
    message = {
        "type": event_type,  # "update" | "anomaly_alert"
        "seller_id": seller_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    await manager.send(seller_id, message)
