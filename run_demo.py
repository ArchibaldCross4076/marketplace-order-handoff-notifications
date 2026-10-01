import json

from src.marketplace_notifications import OrderHandoff, RealtimeClient, notify_handoff


if __name__ == "__main__":
    handoff = OrderHandoff("ord-1042", "seller-7", "buyer-19", "handed_to_carrier", "linen tote")
    result = notify_handoff(RealtimeClient(), handoff)
    print(json.dumps(result, indent=2, sort_keys=True))
