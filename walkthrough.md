# calebsons_cloud_serverless_event_driven_architecture — Walkthrough

A fully local, zero-dependency simulation of a cloud-native, event-driven
serverless architecture. No cloud credentials, no SDKs, no deployments — just
Python standard library.

## Architecture

The project mirrors the shape of an AWS-style event-driven system
(EventBridge/SNS fanning out to Lambda targets), but everything runs in a
single Python process:

- **Producer** — `main.py` loads JSON event fixtures from `events/` and
  publishes them to the local event bus.
- **Event Bus** — `event_bus/local_event_bus.py` implements a synchronous
  publish/subscribe bus that stands in for SNS / EventBridge.
- **Router** — `event_bus/router.py` wires each event type to its handler
  functions, analogous to EventBridge rules or SNS subscriptions.
- **Serverless Functions** — modules in `functions/` act as Lambdas. Each
  receives an event dict, logs activity, and mutates a local "managed
  service" file:
  - `process_order.py` — reacts to `order.created`, updates
    `analytics/analytics_store.json` (`total_orders`, `active_orders`).
  - `update_analytics.py` — reacts to `order.updated` / `order.deleted`,
    updates aggregate metrics in `analytics/analytics_store.json`.
  - `send_notification.py` — reacts to every order event and appends a
    human-readable line to `notifications/outbox.log`.

### ASCII diagram

```
                        ┌──────────────────────────┐
                        │         main.py          │
                        │  (loads events/*.json)   │
                        └─────────────┬────────────┘
                                      │ publish(event)
                                      ▼
                        ┌──────────────────────────┐
                        │     LocalEventBus        │
                        │  (SNS / EventBridge)     │
                        └─────────────┬────────────┘
                                      │ dispatch by event_type
                  ┌───────────────────┼────────────────────┐
                  ▼                   ▼                    ▼
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
         │ process_order   │ │ update_analytics│ │ send_notification   │
         │  (Lambda-like)  │ │  (Lambda-like)  │ │   (Lambda-like)     │
         └────────┬────────┘ └────────┬────────┘ └──────────┬──────────┘
                  │                   │                     │
                  ▼                   ▼                     ▼
         ┌────────────────────────────────────┐   ┌────────────────────┐
         │  analytics/analytics_store.json    │   │ notifications/     │
         │  (DynamoDB-like aggregate store)   │   │   outbox.log       │
         └────────────────────────────────────┘   └────────────────────┘
```

### Event routing table

| Event type      | process_order | update_analytics | send_notification |
|-----------------|:-------------:|:----------------:|:-----------------:|
| `order.created` |       ✓       |                  |         ✓         |
| `order.updated` |               |         ✓        |         ✓         |
| `order.deleted` |               |         ✓        |         ✓         |

## How to run

Requires Python 3.8+. No `pip install` step is required.

```
cd calebsons_cloud_serverless_event_driven_architecture
python main.py
```

You'll see log lines showing:

1. Subscriptions being registered on the bus.
2. Each event being published and dispatched to its handlers.
3. Each handler's side effects (analytics updates, notification writes).

After it runs, inspect:

- `analytics/analytics_store.json` — updated aggregate counters.
- `notifications/outbox.log` — appended notification messages.

## How to run the tests

```
cd calebsons_cloud_serverless_event_driven_architecture
pytest
```

The test suite in `tests/test_event_flow.py`:

- Publishes `order_created.json` and asserts `analytics_store.json` and
  `outbox.log` are updated.
- Runs the full create → update → delete flow and asserts final aggregate
  state and notification count.
- Publishes an unrouted event type and asserts no state changes (no-op).

The fixture resets `analytics_store.json` and `outbox.log` before and after
every test to keep runs deterministic.

## How events flow through the system

1. `main.py` reads each JSON file in `events/`, producing a Python dict with
   at minimum `event_id`, `event_type`, and `data`.
2. `main.py` calls `bus.publish(event)` on a `LocalEventBus` built by
   `event_bus.router.build_event_bus()`.
3. `LocalEventBus.publish` logs the event and delegates to `dispatch`.
4. `dispatch` looks up handlers registered for `event["event_type"]` and
   invokes each one synchronously, in subscription order.
5. Each handler mutates its target file (`analytics_store.json` or
   `outbox.log`) and prints progress to stdout.

## How to add a new event type

1. Create a JSON fixture in `events/`, for example `events/order_refunded.json`:
   ```json
   {
     "event_id": "evt-0004",
     "event_type": "order.refunded",
     "timestamp": "2026-04-20T12:15:00Z",
     "data": {"order_id": "O-1001", "customer": "alice", "amount": 55.00}
   }
   ```
2. Register handlers for the new type in `event_bus/router.py`:
   ```python
   bus.subscribe("order.refunded", update_analytics.handle)
   bus.subscribe("order.refunded", send_notification.handle)
   ```
3. If a handler needs event-type-specific logic, branch on
   `event["event_type"]` inside its `handle` function (see
   `functions/update_analytics.py` for the pattern).
4. Optionally add the new fixture name to `EVENT_FILES_ORDER` in `main.py`
   so the demo run publishes it.

## How to add a new serverless function

1. Create a new module in `functions/`, e.g. `functions/audit_log.py`,
   exposing a `handle(event: dict) -> None` function. Keep the shape
   identical to the existing functions so it stays "Lambda-like".
2. Import it in `event_bus/router.py` and subscribe it to the event types
   it should receive:
   ```python
   from functions import audit_log
   bus.subscribe("order.created", audit_log.handle)
   ```
3. Have it write to its own file under a dedicated directory (e.g.
   `audit/audit.log`) so concerns stay isolated, mirroring how each
   Lambda would target its own managed resource.

## How to extend the architecture

- **Multiple buses / domains** — instantiate more than one `LocalEventBus`
  in `router.py` (e.g. an `orders_bus` and a `billing_bus`) and have
  handlers on one bus re-publish derived events onto another. This mirrors
  cross-account EventBridge fan-out.
- **Async dispatch** — replace the loop in `LocalEventBus.dispatch` with a
  `queue.Queue` + worker threads, or with `asyncio` and async handlers,
  to simulate asynchronous Lambda invocation.
- **Dead-letter queue** — wrap each handler call in `dispatch` with
  try/except and append failed events to a `dlq.log` file.
- **Retries** — add a retry counter and re-dispatch failed events up to N
  times before routing them to the DLQ.
- **Schema validation** — validate events against a JSON schema in
  `publish` before dispatching, to simulate EventBridge schema registries.
- **Persistence** — swap the JSON file store for SQLite (still stdlib)
  to simulate a DynamoDB-style store with queries.
- **Real cloud** — keep the same `handle(event)` signatures and move each
  function to an actual Lambda; the local router becomes EventBridge rules.

## Project layout

```
calebsons_cloud_serverless_event_driven_architecture/
├── analytics/
│   └── analytics_store.json
├── event_bus/
│   ├── local_event_bus.py
│   └── router.py
├── events/
│   ├── order_created.json
│   ├── order_deleted.json
│   └── order_updated.json
├── functions/
│   ├── process_order.py
│   ├── send_notification.py
│   └── update_analytics.py
├── notifications/
│   └── outbox.log
├── tests/
│   └── test_event_flow.py
├── main.py
└── walkthrough.md
```
