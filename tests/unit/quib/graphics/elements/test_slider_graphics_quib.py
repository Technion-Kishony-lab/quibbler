from unittest import mock

import pytest

from pyquibbler import iquib
from pyquibbler.quib.graphics.elements.slider_graphics_function_quib import SliderGraphicsFunctionQuib


@pytest.fixture
def mock_quib():
    return iquib(9)


@pytest.fixture
def slider_quib(mock_quib, axes):
    return SliderGraphicsFunctionQuib.create(
        func=mock.Mock(),
        func_kwargs={
            'ax': axes,
            'valinit': mock_quib
        }
    )


def test_slider_graphics_quib_get_axeses(slider_quib, axes):
    assert slider_quib.get_axeses() == {axes}


def test_slider_graphics_quib_get_value(slider_quib):
    res = slider_quib.get_value()

    res.on_changed.assert_called_once()


def test_slider_graphics_on_change(slider_quib, mock_quib):
    new_value = 4
    slider_quib._on_change(new_value)

    assert mock_quib.get_value() == new_value
