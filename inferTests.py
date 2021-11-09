from infer import inferFromAST
import unittest
import textwrap
import ast
import inspect

def _removeIndent(func):
    src = textwrap.dedent(inspect.getsource(func))
    return ast.parse(src)

def _run(func):
    return inferFromAST(_removeIndent(func))

class TestTypeCheck(unittest.TestCase):
    def test_return_type_int_returns_int(self):
        def f() -> int: 
            return 0

        self.assertEqual(int, _run(f))
        
    def test_return_type_str_returns_str(self):
        def f() -> str: 
            return ""

        self.assertEqual(str, _run(f))       

    def test_return_type_none_infers_type(self):
        def f(): 
            return 0

        self.assertEqual(int, _run(f))


if __name__ == '__main__':
    unittest.main()