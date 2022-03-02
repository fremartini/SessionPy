import inspect
from re import A
from textwrap import dedent

from context import *


def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))


class TestParamTypes(unittest.TestCase):

    def test_lists_empty_list_ok(self):
        def foo():
            xs = []
            ys : List[int] = []
            zs : List[List[int]] = []
        TypeChecker(get_ast(foo))

    def test_lists_good_annotations_ok(self):
        def foo():
            xs = [123, 14, 5]
            ys : List[int] = [1, 2, 3]
            zs : List[List[int]] = [[1,2,3], [4,42], []]
        TypeChecker(get_ast(foo))


    def test_lists_bad_annotations_fails(self):
        def mismatch():
            xs = [123, "oops", 3.1415]
        def wrong_annotation():      
            ys : List[str] = [1, 2, 3]
        def nested():
            zs : List[List[int]] = [[1,"not good",3], [4,2], []]
        for f in [mismatch, wrong_annotation, nested]:
            with self.assertRaises(TypeError):
                TypeChecker(get_ast(f))
 


    def test_lists_annotated_wrong_types_raises_error(self):
        def int_with_string():
            xs : List[int] = ["bad hombre", "not good"]
        def string_with_int():
            xs : List[str] = [4, 42]
        def lists_with_str_lists():
            xs : List[List[str]] = [[4, 42]]
        for f in [int_with_string, string_with_int, lists_with_str_lists]:
            with self.assertRaises(TypeError):
                TypeChecker(get_ast(f))
    
    def test_dicts_empty_dict_ok(self):
        def foo():
            xs = {}
            ys : Dict[int, str] = {}
            zs : Dict[Dict[int, str], int] = {}
        TypeChecker(get_ast(foo))

    def test_dicts_good_annotations_ok(self):
        def foo():
            xs = {"a": 123, "b": 14, "c": 5}
            ys : Dict[str, int] = {"a": 123, "b": 14, "c": 5}
            zs : Dict[str, List[int]] = {"a": [1, 123], "b": [14], "c": []}
        TypeChecker(get_ast(foo))


    def test_dicts_bad_annotations_fails(self):
        def mismatch():
            xs = {"a": 123, "b": 14, "c": "oops"}
        def ill_typed(): 
            ys : Dict[str, int] = {"a": 123, "b": 14, 1: 5}
        def nested_types(): 
            zs : Dict[str, List[int]] = {"a": [1, 123, "bad"], "b": [14], "c": []}
        for f in [mismatch, ill_typed, nested_types]:
            with self.assertRaises(TypeError):
                TypeChecker(get_ast(f))
    
    def test_dict_annotated_wrong_types_raises_error(self):
        def A():
            xs : Dict[int, str] = {2: "valid", 5: False}
        def B():
            xs : Dict[str, int] = {"key": 42, "key2": 100, False: 250} 
        def C():
            xs : Dict[List[str], int] = {[]: 42, ["yes"]: 100, [False]: 1000}
        for f in [A, B, C]:
            with self.assertRaises(TypeError):
                TypeChecker(get_ast(f))

if __name__ == '__main__':
    unittest.main()
