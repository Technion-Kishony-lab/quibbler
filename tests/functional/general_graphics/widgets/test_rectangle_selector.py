import numpy as np
import pytest
from matplotlib import pyplot as plt, widgets

from pyquibbler import iquib
from pyquibbler.quib.graphics import global_collecting
from pyquibbler.quib.graphics.widgets import QRectangleSelector


@pytest.fixture()
def quib():
    return iquib(np.array([0, 100, 0, 100]))


@pytest.fixture
def rectangle_selector_within_another_collector(axes, quib):
    with global_collecting.GraphicsCollector():
        return widgets.RectangleSelector(ax=axes, extents=quib)


def test_rectangle_selector_within_artists_collector_creates_widget(rectangle_selector_within_another_collector):
    assert isinstance(rectangle_selector_within_another_collector, QRectangleSelector)


def test_rectangle_selector_changes_quib(quib, rectangle_selector_within_another_collector):
    new_value = np.array([1, 1, 1, 1])
    rectangle_selector_within_another_collector.extents = new_value

    assert np.array_equal(quib.get_value(), new_value)
