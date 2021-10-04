import numpy as np

from pyquibbler import iquib
from pyquibbler.quib import FunctionQuib


def test_overridden_np_function_called_with_quib_returns_function_quib():
    quib = iquib([1, 2, 3])

    res = np.average(quib)

    assert isinstance(res, FunctionQuib)
    # We assert the value of the result quib is 2 in order to ensure the FunctionQuib was created correctly
    assert res.get_value() == 2


def test_overridden_np_function_called_without_quib_returns_answer():
    res = np.average([1, 2, 3])

    assert res == 2
