import pytest
from unittest import mock

from pyquibbler import iquib
from pyquibbler.quib.graphics.widgets import TextBoxGraphicsFunctionQuib


@pytest.fixture
def mock_quib():
    return iquib('world')


@pytest.fixture
def textbox_quib(mock_quib, axes):
    func_mock = mock.create_autospec(TextBoxGraphicsFunctionQuib.WIDGET_CLS)
    return TextBoxGraphicsFunctionQuib.create(
        func=func_mock,
        func_kwargs={
            'ax': axes,
            'initial': mock_quib,
            'label': ["hello"]
        }
    )


def test_textbox_graphics_quib_get_axeses(textbox_quib, axes):
    assert textbox_quib.get_axeses() == {axes}


def test_textbox_graphics_quib_get_value(textbox_quib):
    res = textbox_quib.get_value()

    res.on_submit.assert_called_once()


def test_radiobuttons_graphics_on_change(textbox_quib, mock_quib):
    textbox_quib._on_change("bye")

    assert mock_quib.get_value() == "bye"
