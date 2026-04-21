"""Local in-memory event bus simulating SNS / EventBridge.

Handlers subscribe to a specific ``event_type`` string. When an event is
published, it is dispatched synchronously to every subscribed handler.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List

Event = Dict[str, Any]
Handler = Callable[[Event], None]


class LocalEventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """Register a handler to be invoked for events of ``event_type``."""
        self._subscribers[event_type].append(handler)
        print(f"[event_bus] subscribed {handler.__name__} -> {event_type}")

    def publish(self, event: Event) -> None:
        """Publish an event to the bus; immediately dispatches to handlers."""
        event_type = event.get("event_type", "<unknown>")
        event_id = event.get("event_id", "<no-id>")
        print(f"[event_bus] publish event_id={event_id} type={event_type}")
        self.dispatch(event)

    def dispatch(self, event: Event) -> None:
        """Route an event to all subscribed handlers for its type."""
        event_type = event.get("event_type", "")
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            print(f"[event_bus] no handlers for {event_type}")
            return
        for handler in handlers:
            print(f"[event_bus] -> {handler.__name__}({event_type})")
            handler(event)

    def subscribers(self, event_type: str) -> List[Handler]:
        return list(self._subscribers.get(event_type, []))
