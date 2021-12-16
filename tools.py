import hashlib, socket

def h(*strs):
    tmp = ''
    for s in strs:
        tmp += str(s)
    return str(hashlib.sha256(tmp.encode()).hexdigest())

def str_to_bytes(s: object) -> bytes:
    return bytes(str(s), 'utf-8')

def bytes_to_str(bs: bytes) -> str:
    return bs.decode('utf-8')

def str_ord(text: str):
    return [ord(_) for _ in text]

def send_context(soc: socket, payload: str, what: str, whom: str):
    print(f'> Sending {what} to {whom}')
    soc.send(str_to_bytes(payload))

def receive_str(soc: socket) -> str:
    bytes, *_ = soc.recvmsg(512)
    return bytes_to_str(bytes)

def send_int(soc: socket, i: int):
    bytes = i.to_bytes(2, 'big')
    soc.send(bytes)

def recv_int(soc: socket) -> int:
    bytes, *_ = soc.recvmsg(512)
    return int.from_bytes(bytes, "big")


