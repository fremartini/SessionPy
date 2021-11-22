from infer import infer_from_ast
import unittest
import textwrap
import ast
import inspect

def _removeIndent(func):
    src = textwrap.dedent(inspect.getsource(func))
    return ast.parse(src)

def _run(func):
    return infer_from_ast(_removeIndent(func))

class TestInferType(unittest.TestCase):
    def test_return_type_int_returns_int(self):
        def f() -> int: 
            return 0

        self.assertEqual(int, _run(f))
        
    def test_return_type_str_returns_str(self):
        def f() -> str: 
            return ""

        self.assertEqual(str, _run(f))       

    def test_return_type_none_infers_type_int(self):
        def f(): 
            return 0

        self.assertEqual(int, _run(f))

    def test_return_type_none_infers_type_str(self):
        def f(): 
            return ""

        self.assertEqual(str, _run(f))

    def test_return_type_given_body_returning_none_returns_none(self):
        def f() -> None:
            print(f"")

        self.assertEqual(None, _run(f))

if __name__ == '__main__':
    unittest.main()