from typing import Generic, TypeVar
T = TypeVar("T")
class Protocol(Generic[T]):
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return "protocol"

    #writeFromStr("Client -> Server : int; Server -> Client : int")
    def writeFromStr(self, p : str) -> None:
        self._write(p)

    #writeFromFile("proto.p")
    def writeFromFile(self, file : str) -> None:
        f = open(file, "r") 
        src = f.read()
        f.close()

        self._write(src)

    def _write(self, s: str) -> None:
        lines = s.split(";")
        roles = dict()

        for line in lines:
            rolePair, typ = [_.strip() for _ in line.split(':')]
            a, b = [x.strip() for x in rolePair.split("->")]

            if not a in roles:
                roles[a] = []
            roles[a].append("send()")
            
            if not b in roles:
                roles[b] = []
            roles[b].append("recv()")

        for role, xs in roles.items():
            with open(f"{role}.py", "w+", encoding='utf-8') as f:
                f.write("### THIS FILE IS AUTOGENERATED, DO NOT EDIT ###\n")
                f.write("from channel import Channel, send, recv\n")

                channelNum = 0
                for x in xs:
                    f.write(f"ch{channelNum}: Channel = Channel(int, {5000 + channelNum})\n")
                    channelNum = channelNum + 1

                channelNum = 0
                for x in xs:
                    f.write(f"ch{channelNum}.{x}\n")
                    channelNum = channelNum + 1