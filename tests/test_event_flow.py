"""End-to-end tests for the local event-driven simulation."""

from __future__ import annotations

import json
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from event_bus.router import build_event_bus  # noqa: E402

ANALYTICS_STORE = os.path.join(PROJECT_ROOT, "analytics", "analytics_store.json")
OUTBOX = os.path.join(PROJECT_ROOT, "notifications", "outbox.log")
EVENTS_DIR = os.path.join(PROJECT_ROOT, "events")


def _reset_state() -> None:
    with open(ANALYTICS_STORE, "w", encoding="utf-8") as fh:
        json.dump({"total_orders": 0, "active_orders": 0, "deleted_orders": 0}, fh, indent=4)
        fh.write("\n")
    os.makedirs(os.path.dirname(OUTBOX), exist_ok=True)
    open(OUTBOX, "w", encoding="utf-8").close()


def _load_store() -> dict:
    with open(ANALYTICS_STORE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_event(name: str) -> dict:
    with open(os.path.join(EVENTS_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(autouse=True)
def clean_state():
    _reset_state()
    yield
    _reset_state()


def test_publish_order_created_updates_analytics_and_outbox():
    bus = build_event_bus()
    event = _load_event("order_created.json")

    bus.publish(event)

    store = _load_store()
    assert store["total_orders"] == 1
    assert store["active_orders"] == 1
    assert store["deleted_orders"] == 0

    with open(OUTBOX, "r", encoding="utf-8") as fh:
        outbox_contents = fh.read()
    assert "order.created" in outbox_contents
    assert event["data"]["order_id"] in outbox_contents


def test_full_event_flow_across_all_event_types():
    bus = build_event_bus()

    bus.publish(_load_event("order_created.json"))
    bus.publish(_load_event("order_updated.json"))
    bus.publish(_load_event("order_deleted.json"))

    store = _load_store()
    assert store["total_orders"] == 1
    assert store["active_orders"] == 0
    assert store["deleted_orders"] == 1
    assert store.get("updated_orders", 0) == 1

    with open(OUTBOX, "r", encoding="utf-8") as fh:
        lines = [line for line in fh.read().splitlines() if line.strip()]
    assert len(lines) == 3
    assert any("order.created" in line for line in lines)
    assert any("order.updated" in line for line in lines)
    assert any("order.deleted" in line for line in lines)


def test_unknown_event_type_is_a_noop():
    bus = build_event_bus()
    bus.publish({"event_id": "evt-x", "event_type": "order.unknown", "data": {"order_id": "O-x"}})

    store = _load_store()
    assert store == {"total_orders": 0, "active_orders": 0, "deleted_orders": 0}
    with open(OUTBOX, "r", encoding="utf-8") as fh:
        assert fh.read() == ""
