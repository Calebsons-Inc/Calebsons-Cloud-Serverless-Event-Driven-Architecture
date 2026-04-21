"""Entry point: simulate a serverless event-driven system end-to-end.

Loads the JSON event fixtures in ``events/`` and publishes them in order to a
:class:`LocalEventBus`. Handlers wired by :mod:`event_bus.router` simulate the
Lambda functions in :mod:`functions`.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

# Make the project root importable when running ``python main.py`` directly.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from event_bus.router import build_event_bus  # noqa: E402

EVENTS_DIR = os.path.join(PROJECT_ROOT, "events")

# Deterministic publish order for the demo run.
EVENT_FILES_ORDER = [
    "order_created.json",
    "order_updated.json",
    "order_deleted.json",
]


def load_events() -> List[Dict[str, Any]]:
    """Load event fixtures from ``events/`` in the demo order."""
    events: List[Dict[str, Any]] = []
    for name in EVENT_FILES_ORDER:
        path = os.path.join(EVENTS_DIR, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            events.append(json.load(fh))
    return events


def run() -> None:
    print("=" * 60)
    print(" calebsons_cloud_serverless_event_driven_architecture ")
    print(" local event-driven simulation")
    print("=" * 60)

    bus = build_event_bus()
    events = load_events()

    print(f"\n[main] loaded {len(events)} event(s) from {EVENTS_DIR}\n")

    for event in events:
        print("-" * 60)
        bus.publish(event)

    print("-" * 60)
    print("[main] done. See analytics/analytics_store.json and notifications/outbox.log")


if __name__ == "__main__":
    run()
