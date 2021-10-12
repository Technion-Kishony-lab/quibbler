from unittest import mock

import pytest

from pyquibbler import iquib
from pyquibbler.quib.graphics.elements.radiobuttons_graphics_function_quib import RadioButtonsGraphicsFunctionQuib


@pytest.fixture
def mock_quib():
    return iquib(0)


@pytest.fixture
def radibuttons_quib(mock_quib, axes):
    return RadioButtonsGraphicsFunctionQuib.create(
        func=mock.Mock(),
        func_kwargs={
            'ax': axes,
            'active': mock_quib,
            'labels': ["bye", "hello"]
        }
    )


def test_radiobuttons_graphics_quib_get_axeses(radibuttons_quib, axes):
    assert radibuttons_quib.get_axeses() == {axes}


def test_radiobuttons_graphics_quib_get_value(radibuttons_quib):
    res = radibuttons_quib.get_value()

    res.on_clicked.assert_called_once()


def test_radiobuttons_graphics_on_change(radibuttons_quib, mock_quib):
    radibuttons_quib._on_change("hello")

    assert mock_quib.get_value() == 1
