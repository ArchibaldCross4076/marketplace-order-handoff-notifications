from src.marketplace_notifications import OrderHandoff, notify_handoff


class FakeClient:
    def __init__(self):
        self.calls = []

    def create_channel(self, channel):
        self.calls.append(("create", channel))
        return {"channel": channel}

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel, event, data, account_id))
        return {"accepted": True}


def test_only_handoff_status_reaches_buyer():
    client = FakeClient()
    pending = OrderHandoff("o1", "s1", "b1", "awaiting_payment", "mug")
    assert notify_handoff(client, pending) is None
    assert client.calls == []

    shipped = OrderHandoff("o1", "s1", "b1", "handed_to_carrier", "mug")
    assert notify_handoff(client, shipped) == {"accepted": True}
    assert client.calls[0] == ("create", "private-buyer-b1")
    assert client.calls[1][2] == "order.handoff"
