import sys
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Geekle import Geekle

def test_geekle():
    new_game = Geekle()
    new_game.word = "ADUMB"
    assert new_game.word == "ADORE", "The Word did not match."