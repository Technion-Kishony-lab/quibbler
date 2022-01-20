import pytest
from unittest.mock import Mock
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.lines import Line2D

from pyquibbler import iquib
from pyquibbler.graphics import global_collecting


@pytest.mark.parametrize("data", [
    [1, 2, 3],
    iquib([1, 2, 3])
])
def test_global_graphics_collecting_mode_happy_flow(axes, data):
    with global_collecting.ArtistsCollector() as collector:
        plt.plot(data)

    assert len(collector.objects_collected) == 1
    assert isinstance(collector.objects_collected[0], Line2D)


def test_global_graphics_collecting_within_collecting(axes):
    with global_collecting.ArtistsCollector() as collector, \
            global_collecting.ArtistsCollector() as nested_collector:
        plt.plot([1, 2, 3])
    assert len(collector.objects_collected) == 1
    assert len(nested_collector.objects_collected) == 1


@pytest.mark.regression
def test_overridden_graphics_function_within_overridden_graphics_function(axes):
    with global_collecting.ArtistsCollector() as collector, global_collecting.overridden_graphics_function():
        with global_collecting.overridden_graphics_function():
            pass
        artist = Artist()

    assert collector.objects_collected == [artist]
