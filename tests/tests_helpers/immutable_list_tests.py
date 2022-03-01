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
        hd = ImmutableList(lst=[1, 2, 3, 4, 5]).head()
        self.assertEqual(hd, 1)

    def test_tails_returns_rest(self):
        tl = ImmutableList(lst=[1, 2, 3, 4, 5]).tail()
        self.assertEqual(tl, ImmutableList(lst=[2, 3, 4, 5]))

    def test_lists_are_equal(self):
        one = ImmutableList(lst=[1, 1, 1])
        two = ImmutableList(lst=[1, 1, 1])
        self.assertEqual(one, two)

    def test_lists_are_not_equal(self):
        one = ImmutableList(lst=[1, 1, 2])
        two = ImmutableList(lst=[1, 1, 1])
        self.assertNotEqual(one, two)


if __name__ == '__main__':
    unittest.main()
