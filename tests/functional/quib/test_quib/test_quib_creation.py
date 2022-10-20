import numpy as np
from matplotlib import pyplot as plt

from pyquibbler import iquib, Quib
from pyquibbler.env import ALLOW_ARRAY_WITH_DTYPE_OBJECT


def test_allow_array_with_dtype_object_off():
    a = iquib(1)
    with ALLOW_ARRAY_WITH_DTYPE_OBJECT.temporary_set(False):
        assert isinstance(np.array([a], dtype=object), np.ndarray)


def test_allow_array_with_dtype_object_on():
    a = iquib(1)
    with ALLOW_ARRAY_WITH_DTYPE_OBJECT.temporary_set(True):
        assert isinstance(np.array([a], dtype=object), Quib)


def test_plot_quib_converts_quib_containing_args_to_quib_arrays():
    a = iquib(1)
    b = plt.plot([0, a, 2])
    arg = b.args[1]
    assert isinstance(arg, Quib) and np.array_equal(arg.get_value(), [0, 1, 2])
