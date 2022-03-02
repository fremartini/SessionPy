import inspect
from textwrap import dedent

from context import *


def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))


class TestParamTypes(unittest.TestCase):
    def test_annotated_list_ints_is_ok(self):
        def foo():
            xs : List[int] = [1, 4, 12, 100, 2000]
        TypeChecker(get_ast(foo))


if __name__ == '__main__':
    unittest.main()
