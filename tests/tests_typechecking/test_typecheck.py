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
        self.assertEqual(tc.get_latest_scope()['res'], int)

    def test_union_int_float_returns_float(self):
        def foo(x: int, y: float) -> float:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        self.assertEqual(tc.get_latest_scope()['res'], float)

    def test_union_float_int_returns_float(self):
        def foo(x: float, y: int) -> float:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        self.assertEqual(tc.get_latest_scope()['res'], float)

    def test_union_float_float_returns_float(self):
        def foo(x: float, y: float) -> float:
            res = x + y
            return res

        tc = TypeChecker(get_ast(foo))
        self.assertEqual(tc.get_latest_scope()['res'], float)

    def test_function_call_matching_argument_type_succeeds(self):
        def foo():
            def inner(x: int) -> int:
                return x

            inner(1)

        TypeChecker(get_ast(foo))

    def test_function_call_different_argument_type_fails(self):
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

    def test_function_call_with_any_return_type_str_succeeds(self):
        def foo(x: Any) -> str:
            return x

        TypeChecker(get_ast(foo))

    def test_function_call_with_any_return_type_int_succeeds(self):
        def foo(x: Any) -> int:
            return x

        TypeChecker(get_ast(foo))

    def test_can_upcast_to_given_int_any_succeeds(self):
        self.assertTrue(can_upcast_to(int, Any))

    def test_can_upcast_to_given_str_any_succeeds(self):
        self.assertTrue(can_upcast_to(str, Any))

    def test_can_upcast_to_given_list_any_succeeds(self):
        self.assertTrue(can_upcast_to(List[str], Any))

    def test_can_upcast_given_float_int_fails(self):
        self.assertFalse(can_upcast_to(float, int))

    # FIXME: does not work
    # def test_can_upcast_given_float_int_fails(self):
    #    self.assertFalse(can_upcast_to(List[int], List[float]))

    def test_can_downcast_given_float_any_succeeds(self):
        self.assertTrue(can_downcast_to(Any, int))

    def test_system_calls_are_ok(self):
        def foo():
            def print_me(x):
                print(x)

            print_me("foo")

        TypeChecker(get_ast(foo))

    def test_type_alias_int_succeeds(self):
        def foo():
            number = int

            def add(x: number, y: number) -> number:
                return x + y

            add(5, 7)

        TypeChecker(get_ast(foo))

    # FIXME: is this implemented yet?
    """
    def test_type_alias_list_int_succeeds(self):
        def foo():
            numList = List[int]

            def length(x: numList) -> int:
                return len(x)

            length([1, 2, 3, 4])

        TypeChecker(get_ast(foo))
    """

    def test_recursion_sum(self):
        def foo():
            def recurse(x: int) -> int:
                if x == 0:
                    return 0

                return x + recurse(x - 1)

            recurse(5)

        TypeChecker(get_ast(foo))

    def test_recursion_fib(self):
        def foo():
            def fib(n):
                if n == 0:
                    return 0
                elif n == 1 or n == 2:
                    return 1
                else:
                    return fib(n - 1) + fib(n - 2)

            fib(5)

        TypeChecker(get_ast(foo))
    """
    #FIXME
    def test_nested_return_statement_succeeds(self):
        def foo(n) -> int:
            if n == 0:
                return 0
            else:
                return 1

        TypeChecker(get_ast(foo))

    def test_nested_return_statement_fails(self):
        def foo(n) -> str:
            if n == 0:
                return 0
            else:
                return 1

        with self.assertRaises(Exception):
            TypeChecker(get_ast(foo))
    """

if __name__ == '__main__':
    unittest.main()
