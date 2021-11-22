import unittest
from typeChecking import *

class TestTypeCheck(unittest.TestCase):
    def test_typeCheck_called_with_correct_argument_type_succeeds(self):
        @typeCheck
        def f(_: int) -> str:
            return ""
        f(1)

    def test_typeCheck_called_with_wrong_argument_type_(self):
        @typeCheck
        def f(_: int) -> str:
            return ""
        
        with self.assertRaises(Exception): f("") 

    def test_typeCheck_given_mismatching_return_type_throws_exception(self):
        with self.assertRaises(Exception):
            @typeCheck
            def f(_: int) -> str:
                return 0

    def test_typeCheck_returning_variable_type_int_has_same_type(self):
        @typeCheck
        def f(x: int) -> int:
            return x

    def test_typeCheck_returning_variable_type_str_has_same_type(self):
        @typeCheck
        def f(x: str) -> str:
            return x

if __name__ == '__main__':
    unittest.main()