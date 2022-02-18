import inspect
from textwrap import dedent

from context import *


def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))


class TestTypeCheck(unittest.TestCase):
    def test_union_int_int_returns_int(self):
        def foo(x: int, y: int) -> int:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        assert (tc.get_latest_scope()['res'] == int)

    def test_union_int_float_returns_float(self):
        def foo(x: int, y: float) -> float:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        assert (tc.get_latest_scope()['res'] == float)

    def test_union_float_int_returns_float(self):
        def foo(x: float, y: int) -> float:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        assert (tc.get_latest_scope()['res'] == float)

    def test_union_float_float_returns_float(self):
        def foo(x: float, y: float) -> float:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        assert (tc.get_latest_scope()['res'] == float)

    def test_function_call_with_matching_arguments_succeeds(self):
        def foo():
            def inner(x: int) -> int:
                return x

            inner(1)

        TypeChecker(get_ast(foo))

    def test_function_call_different_arguments_fails(self):
        def foo():
            def inner(x: int) -> int:
                return x

            inner("asd")

        with self.assertRaises(Exception):
            TypeChecker(get_ast(foo))

    def test_function_call_with_string_expecting_any_succeeds(self):
        def foo():
            def inner(x):
                return x

            inner("asd")

        TypeChecker(get_ast(foo))

    def test_function_call_with_int_expecting_any_succeeds(self):
        def foo():
            def inner(x):
                return x

            inner(42)

        TypeChecker(get_ast(foo))

    def test_function_call_with_str_return_type_any_succeeds(self):
        def foo(x: str) -> Any:
            return x

        TypeChecker(get_ast(foo))

    def test_function_call_with_int_return_type_any_succeeds(self):
        def foo(x: int) -> Any:
            return x

        TypeChecker(get_ast(foo))

if __name__ == '__main__':
    unittest.main()
