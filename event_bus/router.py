"""Wires serverless function handlers to event types on a LocalEventBus.

This is the local equivalent of configuring EventBridge rules / SNS
subscriptions to fan out events to the correct Lambda targets.
"""

from __future__ import annotations

from event_bus.local_event_bus import LocalEventBus
from functions import process_order, send_notification, update_analytics


def build_event_bus() -> LocalEventBus:
    """Create a bus with the default order-domain routes registered."""
    bus = LocalEventBus()

    # order.created: count the new order, notify customer
    bus.subscribe("order.created", process_order.handle)
    bus.subscribe("order.created", send_notification.handle)

    # order.updated: recompute aggregates, notify customer
    bus.subscribe("order.updated", update_analytics.handle)
    bus.subscribe("order.updated", send_notification.handle)

    # order.deleted: recompute aggregates, notify customer
    bus.subscribe("order.deleted", update_analytics.handle)
    bus.subscribe("order.deleted", send_notification.handle)

    # order.refunded: recompute aggregates, notify customer
    bus.subscribe("order.refunded", update_analytics.handle)
    bus.subscribe("order.refunded", send_notification.handle)


    return bus
