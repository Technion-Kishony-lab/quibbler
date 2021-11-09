import numpy as np

from pyquibbler import iquib, q
from pyquibbler.quib import FunctionQuib, ImpureFunctionQuib


def test_overridden_np_function_called_with_quib_returns_function_quib():
    quib = iquib([1, 2, 3])

    res = np.average(quib)

    assert isinstance(res, FunctionQuib)
    # We assert the value of the result quib is 2 in order to ensure the FunctionQuib was created correctly
    assert res.get_value() == 2


def test_overridden_np_function_called_without_quib_returns_answer():
    res = np.average([1, 2, 3])

    assert res == 2


def test_overridden_impure_function_quib_with_no_quib_params_returns_number():
    assert np.random.randint(1, 2) == 1


def test_overridden_impure_function_quib_with_quib_params_returns_quib():
    quib = iquib(2)
    fquib = np.random.randint(1, quib)
    result = fquib.get_value()

    assert isinstance(fquib, ImpureFunctionQuib)
    assert result == 1


def test_can_use_q_on_parameterless_impure_function_quib():
    fquib = q(np.random.rand)
    result1 = fquib.get_value()
    result2 = fquib.get_value()

    assert isinstance(fquib, ImpureFunctionQuib)
    assert isinstance(result1, float)
    assert result1 == result2
