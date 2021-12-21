# A toy-RSA implementation for learning purposes.
# By Johan Irvall Rasmussen
from tools import *

"""
Represents a pair of public and private key.
Can be accessed using key.pub and key.pri.
@input two primes p and q
"""


class KeyPair:
    def __init__(self, p, q) -> None:
        self.p = p
        self.q = q

    def generate(self):
        n = self.p * self.q            # for modulus – part of public key
        Pn = (self.p-1)*(self.q-1)
        lam_n = Pn // (gcd(self.p-1, self.q-1))
        e = None
        for i in range(2, Pn):
            tmp = gcd(Pn, i)
            if tmp == 1:
                e = i
                break
        assert e != None
        assert gcd(e, lam_n) == 1  # e and lam(n) should be co-prime
        d = pow(e, -1, lam_n)
        self.pub = (n, e)
        self.pri = d

    def __str__(self):
        return f'KeyPair(pub={self.pub}, pri={self.pri})'


def sign(plaintext: str, v: int, n: int) -> str:
    return ''.join([chr(ord(ch) ** v % n) for ch in plaintext])


def sign_private(text: str, key: KeyPair) -> str:
    (n, _) = key.pub
    return sign(text, key.pri, n)


def sign_public(text: str, key: KeyPair) -> str:
    (n, e) = key.pub
    return sign(text, e, n)


def commit_hashed(roll: int, rand: str, key: KeyPair):
    msg = h(roll, rand)
    return sign_private(msg, key)


def commit_unhashed(roll: int, rand: str, key: KeyPair):
    (n, _) = key.pub
    msg = str(roll) + rand
    return sign(msg, key.pri, n)


def send_signed(soc: socket, payload: str, what: str, whom: str, key: KeyPair):
    print(f'> Sending {what} to {whom}')
    signed_payload = sign_private(payload, key)
    soc.send(str_to_bytes(signed_payload))


def demo(key: KeyPair):
    # Alice POV
    message = 'hello world'
    signed = (message, sign_private(h(message), key))
    print(f'Sent {signed} to Bob')

    # Bob POV
    msg, sig = signed
    assert h(msg) == sign_public(sig, key)
    print('Math works :)')


# Uncomment for demo:
#k = KeyPair(29, 53)
# k.generate()
# demo(k)
