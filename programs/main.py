def matcher(node: str) -> str:
    match 5 + 2:
        case k if k == 2:
            return "empty"
        case _:
            return "base"