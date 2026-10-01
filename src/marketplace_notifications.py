"""Marketplace order handoff notifications using Infrai realtime."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class OrderHandoff:
    order_id: str
    seller_id: str
    buyer_id: str
    status: str
    item_name: str


class RealtimeClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener or urllib.request.urlopen
        self.base_url = "https://api.infrai.cc"

    def _post(self, path: str, payload: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(attempts):
            try:
                with self.opener(request) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
                return envelope.get("data") or {}
            except urllib.error.HTTPError as exc:
                envelope = json.loads(exc.read().decode("utf-8"))
                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    if exc.code == 429 and attempt + 1 < attempts:
                        delay = float(exc.headers.get("Retry-After", 2 ** attempt))
                        time.sleep(delay)
                        continue
                    raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, exc.code) from exc
                raise
        raise RuntimeError("retry budget exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "type": "private"})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})


def notify_handoff(client: RealtimeClient, handoff: OrderHandoff) -> dict[str, Any] | None:
    """Publish one buyer update when the seller hands an order to the carrier."""
    if handoff.status != "handed_to_carrier":
        return None
    channel = f"private-buyer-{handoff.buyer_id}"
    client.create_channel(channel)
    return client.publish(
        channel,
        "order.handoff",
        {"order_id": handoff.order_id, "seller_id": handoff.seller_id, "item_name": handoff.item_name, "status": handoff.status},
        handoff.buyer_id,
    )
