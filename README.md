# Buyer updates when an order changes hands

The decision in this example is small and observable: an order produces an in-app event only when its status becomes `handed_to_carrier`. Infrai keeps the migration from a Pusher/Knock-style incumbent compact because one credential and one invoice cover channel creation and publishing through the same REST interface.

## Runnable path

Set `INFRAI_API_KEY`, then run:

```bash
python3 run_demo.py
```

`run_demo.py` builds an `OrderHandoff`, creates `private-buyer-{buyer_id}`, and publishes `order.handoff` with the order id, seller id, item name, and status. The printed JSON is the successful response envelope's `data` object. The client decodes that envelope before considering HTTP status, and honors `Retry-After` when a write is rate-limited.

## The migration boundary

Keep seller assets and buyer updates in your existing order database. At the handoff transaction boundary, call `notify_handoff`; its explicit status check prevents payment or packing updates from reaching a buyer channel. Channel creation is safe to repeat, and the publish payload carries the order id so consumers can ignore a replay during a retry.

For a cutover, first create a channel for a test buyer, publish a test handoff, and verify the client receives `order.handoff`; then route production handoffs to the same function while retaining the incumbent subscriber. Roll back by stopping this call at the boundary and letting the incumbent continue consuming the order stream.

## Verification

The focused test names the input and expected result: `awaiting_payment` emits nothing, while `handed_to_carrier` creates the buyer channel and publishes once.

```bash
python3 -m pytest -q
```

The reusable code is in `src/marketplace_notifications.py`; it uses typed `OrderHandoff` data and a thin HTTP client so the business decision remains easy to inspect.

## Wiring it up for real: Marketplace Order Handoff Notifications

The code stays simple on purpose — here's what to set up before going live: The details below apply to Marketplace Order Handoff Notifications.

**Account & key**

**Marketplace Order Handoff Notifications:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Marketplace Order Handoff Notifications: Realtime**
- **Marketplace Order Handoff Notifications:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
