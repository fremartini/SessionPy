from context import union
from typing import List, Tuple
import unittest

class TestTypeCheck(unittest.TestCase):

    def test_int_int_returns_int(self):
        res = union(int, int)
        self.assertEqual(res, int)
    
    def test_int_float_returns_float(self):
        res = union(int, float)
        self.assertEqual(res, float)

    def test_str_int_raises_typeerror(self):
        with self.assertRaises(TypeError):
            union(str, int)

    def test_union_of_user_classes(self):
        class A: ...
        class B(A): ...
        class C: ...
        self.assertEqual(union(A, B), A)
        self.assertEqual(union(B, A), A)
        with self.assertRaises(TypeError):
            union(A, C)

        self.assertEqual(union(List[A], List[B]), List[A])
        self.assertEqual(union(List[Tuple[B,B]], List[Tuple[A,A]]), List[Tuple[A,A]])

    def test_list(self):
        res1 = union(List[int], List[float])
        self.assertEqual(res1, List[float])
        res2 = union(List[List[int]], List[List[float]])
        self.assertEqual(res2, List[List[float]])
    # TODO: More cases

    def test_tuple(self):
        res1 = union(Tuple[int, float], Tuple[float, int])
        self.assertEqual(res1, Tuple[float, float])

        with self.assertRaises(TypeError):
            union(Tuple[any, any], List[any])
    # TODO: More cases


    

if __name__ == '__main__':
    unittest.main()