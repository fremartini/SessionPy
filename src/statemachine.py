from ast import *
from typing import TypeVar, Generic, Any
import typing
from sessiontype import Send, Recv, Offer, Choose, End
from pydoc import locate
import copy
from collections import deque

A = TypeVar('A')


class TSend(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'send'


class TRecv(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'recv'


class TLabel(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'label'


class TOffer(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'offer'


class TChoose(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'choose'


class STEnd:
    def __str__(self) -> str:
        return 'end'

    def __repr__(self) -> str:
        return self.__str__()


class TEps:
    def __str__(self) -> str:
        return 'ε'

    def __repr__(self) -> str:
        return self.__str__()

class TLeft:
    def __repr__(self) -> str:
        return 'left'

class TRight:
    def __repr__(self) -> str:
        return 'right'

class TGoto:
    def __init__(self, lab) -> None:
        self.lab = lab

    def get_label(self):
        return self.lab

    def __repr__(self) -> str:
        return f'goto {self.lab}'

Transition = TSend | TRecv | TChoose | TOffer | TLabel

str_transition_map = {
    "recv": TRecv,
    "send": TSend,
    "offer": TOffer,
    "choose": TChoose,
}


class Node:
    def __init__(self, id: int, accepting_state: bool = False) -> None:
        self.id = id
        self.accepting = accepting_state
        self.outgoing: dict[TSend | TRecv, Node] = {}

    def __str__(self) -> str:
        state = f'(s{self.id})' if self.accepting else f's{self.id}'
        return state

    def is_valid_transition(self, op : str, typ: type = None) -> bool:
        transition = str(self.get_edge()())
        if op == 'recv':
            return transition == op
        else:
            return transition == op and typ == self.outgoing_type()



    def next_nd(self):
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        return list(self.outgoing.values())[0]
        
    def get_edge(self):
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        return list(self.outgoing.keys())[0]
        
    def outgoing_type(self) -> type:
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        key = self.get_edge()
        typ = key.__args__[0]
        assert isinstance(typ, type)
        return typ


def new_node(*args) -> Node:
    return copy.deepcopy(Node(*args))


class STParser(NodeVisitor):
    """
    Parses a sessiontype and stores it in a tuple (self.res):
        parsed = STParser("Channel[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]")
        parsed.res # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
    """

    def __init__(self, src) -> None:
        self.slcs = deque()
        self.labels = set()
        tree = parse(src)
        self.visit(tree)
        self.session_type = self.slcs[0], self.slcs[1]

    def visit_Name(self, node: Name) -> Any:
        match node.id.lower():
            case 'send':
                return TSend()
            case 'recv':
                return TRecv()
            case 'end':
                return STEnd()
            case 'offer':
                return TOffer()
            case 'choose':
                return TChoose()
            case 'label':
                return TLabel()
            case 'channel':
                return None
            case x:
                return locate(x) or x

    def visit_Tuple(self, node: Tuple) -> Any:
        assert len(node.elts) == 2
        t1 = self.visit(node.elts[0])
        if t1 == None:
            t1 = node.elts[0].value
        t2 = self.visit(node.elts[1])
        if t2 == None:
            assert isinstance(node.elts[1], Constant)
            lab_or_goto = node.elts[1].value
            t2 = TGoto(lab_or_goto) if lab_or_goto in self.labels else lab_or_goto
        return t1, t2

    def visit_Subscript(self, node: Subscript) -> Any:
        value = self.visit(node.value)
        slice = self.visit(node.slice)
        if isinstance(value, TLabel):
            assert isinstance(slice[0], str)
            self.labels.add(slice[0])
        #if isinstance(slice[0], str) and slice[0] not in self.labels:
        #    raise Exception()
        assert isinstance(slice, tuple)
        self.slcs.appendleft(slice[1])
        self.slcs.appendleft(slice[0])
        return value, slice

    def visit_Constant(self, node: Constant) -> Any:
        assert isinstance(node.value, str)
        return self.visit(Name(node.value))


    def build(self):
        global ident
        ident = 0

        def next_id():
            global ident
            res = ident
            ident += 1
            return res

        root = new_node(next_id())
        ref = root

        print(self.session_type)

        # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
        st_env = {}
        def go(tup, node: Node):
            if isinstance(tup, STEnd):
                node.accepting = True
                return node, None
            elif isinstance(tup, TGoto):
                lab = tup.get_label()
                assert lab in st_env, (lab, st_env)
                node.outgoing[lab] = st_env[lab]
                return st_env[lab]
            head, tail = tup[0], tup[1]
            head = head.__class__
            if head in [TRecv, TSend]:
                typ = tail[0]
                assert isinstance(typ, type), typ
                nd = new_node(next_id())
                key = head[typ]
                go(tail[1], nd)
                node.outgoing[key] = nd
                return nd, key
            elif head in [TOffer, TChoose]:
                st1, st2 = tail[0], tail[1]
                l, r = new_node(next_id()), new_node(next_id())
                go(st1, l)
                go(st2, r)
                tl, tr = TLeft, TRight
                node.outgoing[tl] = l
                node.outgoing[tr] = r
                return l, r
            elif head in [TLabel]:
                lab = tail[0]
                tl = tail[1]

                self.labels.add(lab)

                st_env[lab] = node
                _, key = go(tl, node)
                return node, key
            else:
                assert head == STEnd or head == str, head
                if head == STEnd:
                    node.accepting = True
                else:
                    return 
                return node, None

        go(self.session_type, ref)
        return root


def print_node(n: Node):
    if not n.outgoing:
        return
    print(n)
    seen = set()
    for key in n.outgoing:
        # TLeft() => left
        # TSend[int].__args__ => (int,)[0]
        # key() =>  
        if key in seen:
            return
        if not isinstance(key, str):
            seen.add(key())
        else:
            seen.add(key)
        if not key in [TLeft, TRight]:
            if isinstance(key, typing._GenericAlias):
                typ = key.__args__[0]
                print(key(), typ, '->', n.outgoing[key])
            else:
                assert isinstance(key, str)
                print('goto', n.outgoing[key])
        else:
            print(key(), '->', n.outgoing[key])
            
   
    print()
    for key in n.outgoing:
        if key in seen:
            return
        seen.add(key)
        n1 = n.outgoing[key]
        if n1.id != n.id:
            print_node(n1)


if __name__ == '__main__':
    st = STParser("Channel[ Label['first', Recv[int, Label['first', Offer[ 'hello', Recv[bool, 'first']]]]]]")
    print(st.session_type)
    print_node(st.build())

