import yaml
import socket
from util import parse

id = 5000
central_port = 5005  # store in config


def generate_id():
    global id
    id += 100
    return id


def projectGlobalProtocol(protoc):
    roles = dict()

    for line in protoc.split(";"):
        if (line.strip() == ""):
            continue
        rolePair, typ = [_.strip() for _ in line.split(':')]
        roleA, roleB = [x.strip() for x in rolePair.split("->")]

        if not roleA in roles:
            roles[roleA] = []
        roles[roleA].append(f"{roleB} : !{typ}")

        if not roleB in roles:
            roles[roleB] = []
        roles[roleB].append(f"{roleA} : ?{typ}")
    return roles


class Conversation:
    def __init__(self, cId, roles) -> None:
        self.cId = cId
        self.roles = roles

    def create(protocol, config):
        id = generate_id()
        parsed_yaml = parse(config)
        print(parsed_yaml)

        # wait for all roles to be filled
        roles = projectGlobalProtocol(protocol)

        c = Conversation(id, roles)
        send("register pls")
        return c

    def join(self, role, principal):
        if role in self.roles:
            send("join pls")
        else:
            print("oh no!")

    def send(self, to_role, payload):
        ...

    def recv(self, role):
        ...

    def stop(self):
        ...


def send(m: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', central_port))
        s.send(bytes(str(m), 'utf-8'))
