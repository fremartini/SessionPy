import unittest
from context import *

class TestVerifyChannels(unittest.TestCase):

    def test_send_succeeds(self):
        @verify_channels
        def main():
            ch = Channel[Send[int, End]]()
            ch.send(42)
            print('sent', 42)  # we expect this!
       
    def test_recv_succeeds(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, End]]()
            v = ch.recv()
            print('received value', v)  # this should happen!

    def test_send_recv_sequence_succeeds(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, Send[bool, End]]]()
            v = ch.recv()
            ch.send(True)
            print('received value', v)  # this should happen!
            print('sent value', True)

    def test_channel_using_function_call_succeeds(test):    
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

    def test_channel_offer_succeeds(self):
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

    def test_channel_branch_succeeds(self):
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

    def test_passing_channel_multiple_times_succeeds(test):
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
    
    def test_unexpected_recv_fails(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Send[int, End]]()
                v = ch.recv()
                print('received', v)  # should never happen
    
    def test_unexpected_send_fails(self):
        with self.assertRaises(Exception):
            @verify_channels
            def main():
                ch = Channel[Recv[int, End]]()
                ch.send(42)
                print('sent value', 42)  # should never happen

    def test_multiple_channels_unexpected_recv_fails(self):
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
    
    
    def test_incorrect_channel_use_in_function_fails(self):
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

    def test_channel_offer_fails(self):
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

    def test_channel_choose_fails(self):
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
    
    def test_channel_recv_ints_can_send_result(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, Recv[int, Send[int, End]]]]()
            x  = ch.recv()
            y  = ch.recv()
            res : int = x+y
            ch.send(res)

    def test_channel_recv_send_same_value_succeeds(self):
        @verify_channels
        def main():
            ch = Channel[Recv[int, Send[int, End]]]()
            x = ch.recv()
            ch.send(x)



if __name__ == '__main__':
    unittest.main()