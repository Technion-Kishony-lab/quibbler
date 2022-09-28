import numpy as np

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
