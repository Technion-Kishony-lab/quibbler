from pyquibbler import iquib
from pyquibbler.quib import override_numpy_functions, FunctionQuib
import numpy as np


def test_overridden_np_function_called_with_quib_returns_function_quib():
    override_numpy_functions()
    quib = iquib([1, 2, 3])

    res = np.average(quib)

    assert isinstance(res, FunctionQuib)
    # We assert the value of the result quib is 2 in order to ensure the FunctionQuib was created correctly
    assert res.get_value() == 2


def test_overridden_np_function_called_without_quib_returns_answer():
    override_numpy_functions()

    res = np.average([1, 2, 3])

    assert res == 2
