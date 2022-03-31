from context import *


class TestTypeCheck(unittest.TestCase):
    def test_new_list_is_empty(self):
        lst = ImmutableList()
        self.assertEqual(lst.len(), 0)

    def test_add_returns_new_list(self):
        lst = ImmutableList()
        new_lst = lst.add('1')
        self.assertEqual(lst.len(), 0)
        self.assertEqual(new_lst.len(), 1)

    def test_head_returns_first_element(self):
        hd = ImmutableList.of_list([1, 2, 3, 4, 5]).head()
        self.assertEqual(hd, 1)

    def test_head_does_not_alter_list(self):
        l = ImmutableList.of_list([1, 2, 3, 4, 5])
        hd = l.head()
        self.assertEqual(hd, 1)
        self.assertEqual(l.len(), 5)

    def test_tail_returns_rest(self):
        tl = ImmutableList.of_list([1, 2, 3, 4, 5]).tail()
        self.assertEqual(tl, ImmutableList.of_list([2, 3, 4, 5]))

    def test_tail_does_not_alter_list(self):
        l = ImmutableList.of_list([1, 2, 3, 4, 5])
        tl = l.tail()
        self.assertEqual(tl, ImmutableList.of_list([2, 3, 4, 5]))
        self.assertEqual(l, ImmutableList.of_list([1, 2, 3, 4, 5]))

    def test_discard_last_discards_last(self):
        l = ImmutableList.of_list([1, 2, 3, 4])
        ls = l.discard_last()
        self.assertEqual(ls, ImmutableList.of_list([1, 2, 3]))

    def test_map_applies_function_over_list(self):
        def addOne(x: int):
            return x + 1

        l = ImmutableList.of_list([1, 2, 3, 4])
        ls = l.map(addOne)
        self.assertEqual(ls, ImmutableList([2, 3, 4, 5]))

    def test_map_applies_lambda_over_list(self):
        l = ImmutableList.of_list([1, 2, 3, 4])
        ls = l.map(lambda x : x + 1)
        self.assertEqual(ls, ImmutableList([2, 3, 4, 5]))

    def test_lists_are_equal(self):
        one = ImmutableList.of_list([1, 1, 1])
        two = ImmutableList.of_list([1, 1, 1])
        self.assertEqual(one, two)

    def test_lists_are_not_equal(self):
        one = ImmutableList.of_list([1, 1, 2])
        two = ImmutableList.of_list([1, 1, 1])
        self.assertNotEqual(one, two)


if __name__ == '__main__':
    unittest.main()
