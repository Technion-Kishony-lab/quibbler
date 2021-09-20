from unittest import mock

import numpy as np
import pytest
from matplotlib import pyplot as plt

from pyquibbler import iquib
from pyquibbler.graphics import override_axes_methods, overriding
from pyquibbler.graphics.overriding import override_applier_functions, override_apply_func, GraphicsFunctionCall
from pyquibbler.quib.holistic_function_quib import HolisticFunctionQuib


@pytest.fixture(autouse=True)
def override():
    override_axes_methods()
    override_applier_functions()


def test_holistic_function_quib_with_numpy_applier():
    argument = iquib([0, 1, 2])

    res = np.apply_along_axis(lambda x: x, 0, argument)

    assert list(res.get_value()) == [0, 1, 2]
    assert isinstance(res, HolisticFunctionQuib)


def test_holistic_function_quib_with_numpy_applier_and_quib_change(monkeypatch):
    argument = iquib([0, 1, 2])
    mock_call = mock.Mock()
    mock_call.return_value = [mock.Mock()]
    graphics_call = GraphicsFunctionCall(func=mock_call, args=tuple(), kwargs={})
    monkeypatch.setattr(overriding, "get_graphics_calls_collected", lambda *_, **__: [graphics_call])

    quib = np.apply_along_axis(lambda x: x, 0, argument)
    argument[0] = 10

    assert list(quib.get_value()) == [10, 1, 2]
    mock_call.assert_called_once()
