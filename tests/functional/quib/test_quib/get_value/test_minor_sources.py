import numpy as np
import pytest

from pyquibbler import iquib


@pytest.mark.regression
def test_array_with_quib_inner_source():
    a = iquib([1])
    b = np.array([a])

    assert b.get_value() == np.array([[1]])
