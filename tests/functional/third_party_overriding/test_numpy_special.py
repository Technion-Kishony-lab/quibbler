import numpy as np
from numpy import ogrid, mgrid
from numpy.lib._index_tricks_impl import nd_grid

from pyquibbler import iquib


def test_orgrid_getitem_without_quibs():
    grid = mgrid[0:3]
    assert np.array_equal(grid, [0, 1, 2])


def my_getitem(self, key):
    return key


def test_orgrid_getitem_with_quibs():
    n = iquib(3)
    grid = mgrid[0:n]
    assert np.array_equal(grid.get_value(), [0, 1, 2])



