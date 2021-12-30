import unittest
from channel import Branch, Channel
from sessiontype import *

from typechecking import verify_channels

class TestVerifyChannels(unittest.TestCase):

    def test_good1(self):
        @verify_channels
        def main():
            ch = Channel[Send[int, End]]()
            ch.send(42)
            print('sent', 42)  # we expect this!
       
    def test_good2(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, End]]()
            v = ch.recv()
            print('received value', v)  # this should happen!

    def test_good3(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, Send[bool, End]]]()
            v = ch.recv()
            ch.send(True)
            print('received value', v)  # this should happen!
            print('sent value', True)

    def test_good4(test):    
        @verify_channels
        def main():
            def inner(c: Channel):
                v = c.recv()
                # this should happen! expecting a receive
                print('received value', 666)
                return v

            ch = Channel[Send[int, Recv[bool, Send[str, End]]]]()
            ch.send(42)
            print('sent value', True)
            inner(ch)
            ch.send("we're done here...")  # ending the session

    def test_good5(self):
        @verify_channels
        def main():
            ch = Channel[Send[int, Offer[Send[str, Recv[str, End]], Send[int, End]]]]()
            ch.send(5)

            match ch.offer():
                case Branch.LEFT:
                    print("A: receiving message from client (B)")
                    ch.send("hello!")
                    msg = ch.recv()
                    print(f"A: received message '{msg}'")

                case Branch.RIGHT:
                    print("A: sending number to client (B)")
                    ch.send(42)

    def test_good6(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, Choose[Send[str, End], Choose[Send[str, End], Recv[int, End]]]]]()
            n = ch.recv()

            if 10 > 5:
                ch.choose(Branch.LEFT)
                ch.send("number was greater than 5")
            else:
                ch.choose(Branch.RIGHT)
                if 1 + 3 > 4:
                    ch.choose(Branch.LEFT)
                    ch.send("hi")
                else:
                    ch.choose(Branch.RIGHT)
                    i = ch.recv()

    def test_passing_channel_multiple_times_should_be_okay(test):
        @verify_channels
        def main():
            def f(c: Channel):
                v = c.recv()
                g(v, c)

            def g(i: int, chan: Channel):
                res = 'incremented by one is ' + str(i + 1)
                chan.send("yup, i did it")

            ch = Channel[Send[int, Recv[int, Send[str, End]]]]()
            ch.send(42)
            print('sent value', True)
            f(ch)
    
    def test_bad1(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Send[int, End]]()
                v = ch.recv()
                print('received', v)  # should never happen
    
    def test_bad2(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Recv[int, End]]()
                ch.send(42)
                print('sent value', 42)  # should never happen

    def test_bad3(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Send[int, Recv[bool, End]]]()
                ch1 = Channel[Recv[str, Send[int, End]]]()
                ch.send(True)
                v = ch1.recv()
                # this should NOT happen - wrong type!
                print('received value', v)
                print('sent value', True)
    
    
    def test_bad4(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                def f(c: Channel):
                    b = c.recv()
                    # should happen; at this point we receive
                    print('received value', b)
                    return b
                ch = Channel[Send[int, Recv[bool, Send[str, End]]]]()
                ch.send(42)
                print('sent value', True)  # okay so far
                f(ch)
                s = ch.recv()
                # should NOT happen; at this point we should send
                print('received', s)

    def test_bad5(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Send[int, Offer[Send[str, Recv[int, End]], Send[int, End]]]]()
                ch.send(5)

                match ch.offer():
                    case Branch.LEFT:
                        print("A: receiving message from client (B)")
                        ch.send("hello!")

                    case Branch.RIGHT:
                        print("A: sending number to client (B)")
                        ch.send(42)

    def test_bad6(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Recv[int, Choose[Send[str, End], Choose[Send[int, End], Recv[int, End]]]]]()
                n = ch.recv()

                if 10 > 5:
                    ch.choose(Branch.LEFT)
                    ch.send("number was greater than 5")
                else:
                    ch.choose(Branch.RIGHT)
                    if 1 + 3 > 4:
                        ch.choose(Branch.LEFT)
                        ch.send(1)
                    else:
                        ch.choose(Branch.RIGHT)
    
if __name__ == '__main__':
    unittest.main()