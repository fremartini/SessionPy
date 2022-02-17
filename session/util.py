def channels_str(channels):
    res = ''
    for ch_name in channels:
        res += f'"{ch_name}": {channels[ch_name]}\n'
    return res

def strToTyp(s):
    match s:
        case 'int': return int
        case 'str': return str
        case 'bool': return bool
        case _: raise Exception(f"unknown type {s}")

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected " + str(expected) + ", found " + str(actual))