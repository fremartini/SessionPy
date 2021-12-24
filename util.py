import socket
import ast
import yaml
import pickle


def dump(s, obj):
    print(s, "=")
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))
    print()


def dump_ast(exp):
    print(ast.dump(exp, indent=4))


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


def parse(config):
    with open(config, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def serialize(obj):
    return pickle.dumps(obj)


def deserialize(obj):
    return pickle.loads(obj)


def load_router_config():
    return parse("config.yml")['router']


def channels_str(channels):
    res = ''
    for ch_name in channels:
        res += f'"{ch_name}": {channels[ch_name]}\n'
    return res

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected " + str(expected) + ", found " + str(actual))