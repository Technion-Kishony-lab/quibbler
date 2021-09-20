from unittest import mock

import numpy as np
import pytest

from pyquibbler import iquib, graphics
from pyquibbler.graphics import GraphicsFunctionCall
from pyquibbler.quib import override_numpy_functions
from pyquibbler.quib.holistic_function_quib import HolisticFunctionQuib


@pytest.fixture(autouse=True)
def override():
    override_numpy_functions()


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
    monkeypatch.setattr(graphics, "get_graphics_calls_collected", lambda *_, **__: [graphics_call])

    quib = np.apply_along_axis(lambda x: x, 0, argument)
    argument[0] = 10

    assert list(quib.get_value()) == [10, 1, 2]
    mock_call.assert_called_once()
