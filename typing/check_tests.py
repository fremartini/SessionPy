import unittest

from check import typecheck_file


def exec_file(file) -> None:
    typecheck_file(f'tests/{file}')


class TestTypeCheck(unittest.TestCase):

    def test_succeed(self):
        exec_file('main.py')

    # def test_fails(self):
    #    with self.assertRaises(Exception):
    #        self.exec_file('main.py')


if __name__ == '__main__':
    unittest.main()
