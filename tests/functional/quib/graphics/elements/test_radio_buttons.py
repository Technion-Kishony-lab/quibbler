import pytest
from unittest import mock

from pyquibbler import iquib
from pyquibbler.quib.graphics.widgets import RadioButtonsGraphicsFunctionQuib


@pytest.fixture
def mock_quib():
    return iquib(0)


@pytest.fixture
def radibuttons_quib(mock_quib, axes):
    func_mock = mock.create_autospec(RadioButtonsGraphicsFunctionQuib.WIDGET_CLS)
    return RadioButtonsGraphicsFunctionQuib.create(
        func=func_mock,
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
