import numpy as np
import pytest
from matplotlib import pyplot as plt, widgets

from pyquibbler import iquib
from pyquibbler.general_graphics import QRectangleSelector


@pytest.fixture()
def quib():
    return iquib(np.array([0, 100, 0, 100]))


@pytest.fixture
def rectangle_selector_widget(axes, quib):
    selector = QRectangleSelector(ax=axes, extents=quib.get_value())
    selector._quibbler_args_dict = {'extents': quib}
    return selector


def test_rectangle_selector_changes_quib(quib, rectangle_selector_widget):
    new_value = np.array([1, 1, 1, 1])
    rectangle_selector_widget.extents = new_value

    assert np.array_equal(quib.get_value(), new_value)
