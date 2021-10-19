import pytest
from unittest import mock
from pyquibbler import iquib
from pyquibbler.quib.graphics.widgets import CheckButtonsGraphicsFunctionQuib


@pytest.fixture
def mock_quib():
    return iquib([False, True])


@pytest.fixture
def checkbuttons_quib(mock_quib, axes):
    func_mock = mock.create_autospec(CheckButtonsGraphicsFunctionQuib.WIDGET_CLS)
    return CheckButtonsGraphicsFunctionQuib.create(
        func=func_mock,
        func_kwargs=dict(ax=axes, actives=mock_quib, labels=['hello','world'])
    )


def test_checkbuttons_graphics_quib_get_axeses(checkbuttons_quib, axes):
    assert checkbuttons_quib.get_axeses() == {axes}


def test_checkbuttons_graphics_quib_get_value(checkbuttons_quib):
    res = checkbuttons_quib.get_value()

    res.on_clicked.assert_called_once()


def test_checkbuttons_graphics_on_change(checkbuttons_quib, mock_quib):
    new_value = 'world'
    checkbuttons_quib._on_change(new_value)
    # I have a problem implementing this test:
    #assert mock_quib.get_value() == [True,True]
