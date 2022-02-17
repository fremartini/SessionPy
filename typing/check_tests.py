import unittest
from check import check
from typing import *
import os

class TestTypeCheck(unittest.TestCase):

    def run(self, file):
        with open(f'tests/{file}', "r") as f:
                    obj = f.read()
                    print("obj ---> \n", obj)
                    exec(obj)

    #TEST_FILES_SUCCEED = os.listdir('tests/succeed')
    #TEST_FILES_FAIL = os.listdir('tests/fail')
    """
    def __init__(self, methodName: str = ...) -> None:
        global TEST_FILES_SUCCEED
        global TEST_FILES_FAIL
        (exec(file) for file in TEST_FILES_SUCCEED)

        for file in TEST_FILES_FAIL:
            try:
                exec(file)
                print(f'{file} did not fail')
            except Exception:
                ...
    """

    def test_succeed(self):
        self.run('main.py')

    #def test_fails(self):
    #    with self.assertRaises(Exception):


if __name__ == '__main__':
    unittest.main()