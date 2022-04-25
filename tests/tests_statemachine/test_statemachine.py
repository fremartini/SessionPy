from context import *


class TestStatemachine(unittest.TestCase):

    def test_stparser_given_send_int_has_single_outgoing_edge(self):
        graph = STParser("Channel[Send[int, End]]").build()
        self.assertEqual(len(graph.outgoing), 1)

    def test_stparser_given_send_int_has_correct_edge_type(self):
        graph = STParser("Channel[Send[int, End]]").build()
        send_int = Transition(Action.SEND)
        send_int.typ = int
        self.assertTrue(send_int in graph.outgoing)

    def test_stparser_given_send_int_has_accepting_end_node(self):
        graph = STParser("Channel[Send[int, End]]").build()
        self.assertTrue(graph.next_nd().accepting)

    def test_stparser_given_offer_has_two_outgoing_edges(self):
        graph = STParser("Channel[Offer[Send[int, End],Recv[int, End]]]").build()
        self.assertEqual(len(graph.outgoing), 2)

    def test_stparser_given_offer_edges_have_correct_types(self):
        graph = STParser("Channel[Offer[Send[int, End],Recv[int, End]]]").build()
        self.assertTrue(Branch.LEFT in graph.outgoing)
        self.assertTrue(Branch.RIGHT in graph.outgoing)

    def test_stparser_given_choose_has_two_outgoing_edges(self):
        graph = STParser("Channel[Choose[Send[int, End],Recv[int, End]]]").build()
        self.assertEqual(len(graph.outgoing), 2)

    def test_stparser_given_choose_edges_have_correct_types(self):
        graph = STParser("Channel[Choose[Send[int, End],Recv[int, End]]]").build()
        self.assertTrue(Branch.LEFT in graph.outgoing)
        self.assertTrue(Branch.RIGHT in graph.outgoing)

    def test_stparser_given_label_builds_circular_reference(self):
        graph = STParser("Channel[Label[\"loop\", Send[int, \"loop\"]]]").build()
        self.assertEqual(graph.next_nd(), graph)


if __name__ == '__main__':
    unittest.main()
