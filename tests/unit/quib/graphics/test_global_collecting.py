from unittest.mock import Mock

import pytest
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.lines import Line2D

from pyquibbler import iquib
from pyquibbler.quib.graphics import global_collecting
from pyquibbler.quib.graphics.global_collecting import AlreadyCollectingArtistsException, QuibDependencyCollector


@pytest.mark.parametrize("data", [
    [1, 2, 3],
    iquib([1, 2, 3])
])
def test_global_graphics_collecting_mode_happy_flow(axes, data):
    with global_collecting.ArtistsCollector() as collector:
        plt.plot(data)

    assert len(collector.artists_collected) == 1
    assert isinstance(collector.artists_collected[0], Line2D)


def test_global_graphics_collecting_raises_exception_when_within_collector():
    with pytest.raises(AlreadyCollectingArtistsException):
        with global_collecting.ArtistsCollector(), global_collecting.ArtistsCollector(raise_if_within_collector=True):
            pass


def test_global_graphics_collecting_when_within_collector():
    with global_collecting.ArtistsCollector():
        assert global_collecting.is_within_artists_collector()


def test_global_graphics_collecting_when_not_within_collector():
    with global_collecting.ArtistsCollector():
        pass

    assert global_collecting.is_within_artists_collector() is False


def test_global_graphics_collecting_within_collecting(axes):
    with global_collecting.ArtistsCollector() as collector, \
            global_collecting.ArtistsCollector() as nested_collector:
        plt.plot([1, 2, 3])
    assert len(collector.artists_collected) == 1
    assert len(nested_collector.artists_collected) == 1


@pytest.mark.regression
def test_global_graphics_collecting_within_collecting_is_within_collector(axes):
    with global_collecting.ArtistsCollector():
        with global_collecting.ArtistsCollector():
            pass
        assert global_collecting.is_within_artists_collector()


@pytest.mark.regression
def test_overridden_graphics_function_within_overridden_graphics_function(axes):
    with global_collecting.ArtistsCollector() as collector, global_collecting.overridden_graphics_function():
        with global_collecting.overridden_graphics_function():
            pass
        artist = Artist()

    assert collector.artists_collected == [artist]


def test_quib_dependency_collector():
    dep1a = Mock()
    dep1b = Mock()
    dep2 = Mock()

    with QuibDependencyCollector.collect() as collected1:
        QuibDependencyCollector.add_dependency(dep1a)
        with QuibDependencyCollector.collect() as collected2:
            QuibDependencyCollector.add_dependency(dep2)
        QuibDependencyCollector.add_dependency(dep1b)

    assert collected1 == {dep1a, dep1b}
    assert collected2 == {dep2}
