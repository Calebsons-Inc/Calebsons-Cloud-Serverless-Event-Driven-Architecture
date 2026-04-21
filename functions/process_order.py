"""Serverless function: process_order.

Simulates a Lambda that reacts to ``order.created`` events. It records the
new order in the analytics store by incrementing ``total_orders`` and
``active_orders``.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYTICS_STORE = os.path.join(PROJECT_ROOT, "analytics", "analytics_store.json")


def _load_store() -> Dict[str, int]:
    with open(ANALYTICS_STORE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_store(store: Dict[str, int]) -> None:
    with open(ANALYTICS_STORE, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=4)
        fh.write("\n")


def handle(event: Dict[str, Any]) -> None:
    order_id = event.get("data", {}).get("order_id", "<unknown>")
    print(f"[process_order] processing new order {order_id}")

    store = _load_store()
    store["total_orders"] = store.get("total_orders", 0) + 1
    store["active_orders"] = store.get("active_orders", 0) + 1
    _save_store(store)

    print(
        f"[process_order] analytics updated total={store['total_orders']} "
        f"active={store['active_orders']}"
    )
