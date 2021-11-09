from typeChecking import *

class Channel:
    def __init__(self, typ):
        self.chType = typ
        self.queue = []

    def __str__(self) -> str:
        return f"Channel{str(self.chType)} {str(self.queue)}"

def send(ch : Channel, e: int) -> str:
    ch.queue.append(e)
    print(f"appended {e}: {ch.queue}")

def recv(ch : Channel):
    v = ch.queue.pop(0)
    print(f"poppped {v} from queue")
    return v