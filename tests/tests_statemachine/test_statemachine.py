from context import *


class TestStatemachine(unittest.TestCase):

    def test_stparser_given_send_int_has_single_outgoing_edge(self):
        graph = STParser("Channel[Send[List[int], End]]").build()
        self.assertEqual(len(graph.outgoing), 1)

    def test_stparser_given_send_int_has_accepting_end_node(self):
        graph = STParser("Channel[Send[List[int], End]]").build()
        self.assertTrue(graph.next_nd().accepting)

    def test_stparser_given_offer_has_two_outgoing_edges(self):
        graph = STParser("Channel[Offer[Send[int, End],Recv[int, End]]]").build()
        self.assertEqual(len(graph.outgoing), 2)


if __name__ == '__main__':
    unittest.main()
