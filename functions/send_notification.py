"""Serverless function: send_notification.

Simulates a Lambda that reacts to any order event and appends a
human-readable message to ``notifications/outbox.log``.
"""

from __future__ import annotations

import datetime as _dt
import os
from typing import Any, Dict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.path.join(PROJECT_ROOT, "notifications", "outbox.log")

_MESSAGES = {
    "order.created": "Your order {order_id} has been received. Thank you, {customer}!",
    "order.updated": "Your order {order_id} was updated, {customer}.",
    "order.deleted": "Your order {order_id} has been cancelled, {customer}.",
}


def _format_message(event: Dict[str, Any]) -> str:
    event_type = event.get("event_type", "")
    data = event.get("data", {})
    template = _MESSAGES.get(event_type, "Event {event_type} received for order {order_id}.")
    return template.format(
        event_type=event_type,
        order_id=data.get("order_id", "<unknown>"),
        customer=data.get("customer", "customer"),
    )


def handle(event: Dict[str, Any]) -> None:
    message = _format_message(event)
    timestamp = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    line = f"{timestamp} [{event.get('event_type', '')}] {message}"

    print(f"[send_notification] {message}")

    os.makedirs(os.path.dirname(OUTBOX), exist_ok=True)
    with open(OUTBOX, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
