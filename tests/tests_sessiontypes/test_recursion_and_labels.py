

import unittest
from context import *

class TestRecAndLab(unittest.TestCase):

    def test_forward_ref_ok(self):
        def ok():
            ch = Channel[Offer[  Send[int, 'jump'],  Recv[str, Label['jump', Recv[bool, End]]]   ]]()
            match ch.offer():
                case Branch.LEFT:
                    ch.send(42)
                    b = ch.recv()
                case Branch.RIGHT:
                    s = ch.recv()
                    b = ch.recv()
        TypeChecker(get_ast(ok))
    
    def test_forward_ref_ill_typed(self):
        def fail():
            ch = Channel[Offer[  Send[int, 'jump'],  Recv[str, Label['jump', Recv[bool, End]]]   ]]()
            match ch.offer():
                case Branch.LEFT:
                    ch.send(42)
                    # Err! Should receive bool here
                case Branch.RIGHT:
                    s = ch.recv()
                    b = ch.recv()
        with self.assertRaises(SessionException):
            TypeChecker(get_ast(fail))

    def test_simple_while_loop(self):
        def ok():
            ch = Channel[Send[bool, Label["repeat", Recv[str, Send[int, "repeat"]]]]]()
            ch.send(2 < 3)
            while True:
                s = ch.recv()
                ch.send(42)
        TypeChecker(get_ast(ok))


    def test_offer_inside_while(self):
        def ok():
            ch = Channel[Label['main', Choose [Send[int, Recv[str, 'main'] ], Recv[bool, Send[float, 'main' ]]]]]()
            while True:
                if 2 < 15:
                    ch.choose(Branch.RIGHT)
                    b = ch.recv()
                    ch.send(3.14)
                else:
                    ch.choose(Branch.LEFT)
                    ch.send(12)
                    ch.recv()
        TypeChecker(get_ast(ok))

if __name__ == '__main__':
    unittest.main()