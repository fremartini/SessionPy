class SessionData:
    recipient_addr = None
    payload = None

    def __init__(self, addr, payload) -> None:
        self.recipient_addr = addr
        self.payload = payload

    def __str__(self) -> str:
        return f"SessionData: (addr: {self.recipient_addr}, payload: {self.payload})"
