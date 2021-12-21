import time
import hashlib
import random
import string
import socket


def rand_str(n: int):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))


def h(*strs):
    tmp = ''
    for s in strs:
        tmp += str(s)
    return str(hashlib.sha256(tmp.encode()).hexdigest())


def str_to_bytes(s: object) -> bytes:
    return bytes(str(s), 'utf-8')


def bytes_to_str(bs: bytes) -> str:
    return bs.decode('utf-8')


def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)


def read_pub(s):
    n, e = [int(_) for _ in s[1:-1].split(',')]
    return n, e


def str_ord(text: str):
    return [ord(_) for _ in text]


def send_context(soc: socket, payload: str, what: str, whom: str):
    print(f'> Sending {what} to {whom}')
    soc.send(str_to_bytes(payload))


def receive(soc: socket) -> str:
    bytes, *_ = soc.recvmsg(512)
    return bytes_to_str(bytes)


def receive_int(soc: socket) -> int:
    bytes, *_ = soc.recvmsg(512)
    return int.from_bytes(bytes, "big")


def dice_roll():
    return random.randint(1, 6)
