class Protocol():
    def __init__(self, protoc : str) -> None:
        self.protoc = protoc

    def __str__(self) -> str:
        return self.protoc

    def projectGlobalProtocol(self):
        roles = dict()

        for line in self.protoc.split(";"):
            if (line.strip() == ""): continue
            rolePair, typ = [_.strip() for _ in line.split(':')]
            roleA, roleB = [x.strip() for x in rolePair.split("->")]

            if not roleA in roles:
                roles[roleA] = []
            roles[roleA].append(f"{roleB} : !{typ}")
            
            if not roleB in roles:
                roles[roleB] = []
            roles[roleB].append(f"{roleA} : ?{typ}")

        return roles