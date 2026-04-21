"""Serverless function: update_analytics.

Simulates a Lambda that reacts to ``order.updated`` and ``order.deleted``
events and maintains aggregate metrics in ``analytics/analytics_store.json``.
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
    event_type = event.get("event_type", "")
    order_id = event.get("data", {}).get("order_id", "<unknown>")
    print(f"[update_analytics] recomputing metrics for {order_id} ({event_type})")

    store = _load_store()
    if event_type == "order.deleted":
        store["deleted_orders"] = store.get("deleted_orders", 0) + 1
        store["active_orders"] = max(0, store.get("active_orders", 0) - 1)
    elif event_type == "order.updated":
        # Aggregated metric example: count updates-in-place as a side counter.
        store["updated_orders"] = store.get("updated_orders", 0) + 1
    _save_store(store)

    print(
        f"[update_analytics] store active={store.get('active_orders', 0)} "
        f"deleted={store.get('deleted_orders', 0)} "
        f"updated={store.get('updated_orders', 0)}"
    )
