import matplotlib.pyplot as plt
import numpy as np
import pytest
from unittest import mock

from pyquibbler import iquib
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.graphics import GraphicsFunctionQuib, global_collecting


class MockArtistsCollector:
    def __init__(self, mock_axes):
        self.mock_axes = mock_axes
        self.all_mock_artists_created = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _create_mock_artist(self):
        artist = mock.Mock()
        artist.axes = self.mock_axes
        self.mock_axes.artists.append(artist)
        return artist

    @property
    def artists_collected(self):
        artist = self._create_mock_artist()
        self.all_mock_artists_created.append(artist)
        return [artist]


@pytest.fixture()
def mock_axes():
    axes = mock.Mock()
    axes.artists = []
    return axes


@pytest.fixture
def mock_artists_collector(monkeypatch, mock_axes):
    mock = MockArtistsCollector(mock_axes)
    monkeypatch.setattr(global_collecting, "ArtistsCollector", lambda: mock)
    return mock


def get_graphics_quib(func, args=()):
    return GraphicsFunctionQuib(
        args=args,
        kwargs={},
        cache_behavior=None,
        func=func,
        artists=[]
    )


def test_graphics_function_quib_get_value_returns_value():
    mock_func = mock.Mock(return_value='mock_func.return_value')
    quib = get_graphics_quib(mock_func)

    res = quib.get_value()

    assert res == mock_func.return_value


@pytest.mark.regression
def test_graphics_function_quib_calculates_even_if_it_has_graphics_that_were_removed():
    parent = iquib(10)

    def func(x):
        plt.plot(x)
        return x + 1

    quib = GraphicsFunctionQuib.create_wrapper(func)(parent)
    first_value = quib.get_value()
    plt.cla()
    parent.invalidate_and_redraw_at_path([])

    assert quib.get_value() == first_value


def test_graphics_function_quib_rerun_removes_artists_created(mock_axes, mock_artists_collector):
    father_quib = iquib(1)
    quib = get_graphics_quib(mock.Mock())
    father_quib.add_child(quib)

    quib.get_value()
    father_quib.invalidate_and_redraw_at_path(path=[PathComponent(component=..., indexed_cls=np.ndarray)])

    assert len(mock_artists_collector.all_mock_artists_created) == 2
    assert len(mock_axes.artists) == 1
