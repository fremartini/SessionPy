from context import *


class TestTypeCheck(unittest.TestCase):
    def test_new_map_is_empty(self):
        m = ImmutableMap()
        self.assertEqual(m.len(), 0)

    def test_add_returns_new_map(self):
        m = ImmutableMap()
        new_m = m.add('1', 1)
        self.assertEqual(m.len(), 0)
        self.assertEqual(new_m.len(), 1)

    def test_contains_given_existing_key_returns_true(self):
        m = ImmutableMap(map={'exists': True})
        self.assertTrue(m.contains('exists'))

    def test_contains_given_non_existing_key_returns_false(self):
        m = ImmutableMap()
        self.assertFalse(m.contains('exists'))

    def test_lookup_given_existing_key_returns_value(self):
        m = ImmutableMap(map={'1': 1, '2': 2})
        self.assertEqual(m.lookup('1'), 1)

    def test_lookup_given_non_existing_key_throws_exception(self):
        with self.assertRaises(Exception):
            m = ImmutableMap(map={'1': 1})
            m.lookup('2')

    def test_lookup_or_default_given_existing_key_returns_value(self):
        m = ImmutableMap(map={'1': 1, '2': 2})
        self.assertEqual(m.lookup_or_default('1', 5), 1)

    def test_lookup_or_default_given_non_existing_key_returns_default(self):
        m = ImmutableMap(map={'2': 2})
        self.assertEqual(m.lookup_or_default('1', 5), 5)

    def test_maps_are_equal(self):
        one = ImmutableMap(map={'1': 1, '2': 2})
        two = ImmutableMap(map={'1': 1, '2': 2})
        self.assertEqual(one, two)

    def test_maps_are_equal_unordered(self):
        one = ImmutableMap(map={'2': 2, '1': 1})
        two = ImmutableMap(map={'1': 1, '2': 2})
        self.assertEqual(one, two)

    def test_maps_are_not_equal(self):
        one = ImmutableMap(map={'1': 1, '2': 2})
        two = ImmutableMap(map={'3': 2, '2': 2})
        self.assertNotEqual(one, two)


if __name__ == '__main__':
    unittest.main()