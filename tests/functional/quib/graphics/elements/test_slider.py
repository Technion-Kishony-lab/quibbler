import pytest
from unittest import mock
from pyquibbler import iquib
from pyquibbler.quib.graphics.widgets import SliderGraphicsFunctionQuib


@pytest.fixture
def mock_quib():
    return iquib(9)


@pytest.fixture
def slider_quib(mock_quib, axes):
    func_mock = mock.create_autospec(SliderGraphicsFunctionQuib.WIDGET_CLS)
    func_mock.return_value.drag_active = lambda x: False
    return SliderGraphicsFunctionQuib.create(
        func=func_mock,
        func_kwargs=dict(ax=axes, valinit=mock_quib, label='Whatever', valmin=0, valmax=1)
    )


def test_slider_graphics_quib_get_axeses(slider_quib, axes):
    assert slider_quib.get_axeses() == {axes}


def test_slider_graphics_quib_get_value(slider_quib):
    res = slider_quib.get_value()

    res.on_changed.assert_called_once()

