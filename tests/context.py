import os
import unittest
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typecheck.check import *
from session.channel import *
from session.typechecking import *
