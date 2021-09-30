from unittest import mock

import pytest

from pyquibbler import CacheBehavior, iquib
from pyquibbler.quib.graphics import GraphicsFunctionQuib, global_collecting


@pytest.fixture()
def mock_axes():
    axes = mock.Mock()
    axes.artists = []
    return axes


@pytest.fixture()
def create_mock_artist(mock_axes):
    def _create():
        artist = mock.Mock()
        artist.axes = mock_axes
        mock_axes.artists.append(artist)
        return artist
    return _create


@pytest.fixture()
def mock_artists_collected(create_mock_artist, monkeypatch):
    # artists = [create_mock_artist()]
    monkeypatch.setattr(global_collecting, "get_artists_collected", lambda *_, **__: [create_mock_artist()])
    return artists


def test_graphics_function_quib_get_value_returns_value():
    mock_func = mock.Mock(return_value='mock_func.return_value')
    quib = GraphicsFunctionQuib(
        args=tuple(),
        kwargs={},
        cache_behavior=CacheBehavior.ON,
        func=mock_func,
        artists=[]
    )

    res = quib.get_value()

    assert res == mock_func.return_value


def test_graphics_function_quib_rerun_removes_artists_created(monkeypatch, mock_axes, create_mock_artist):
    all_mock_artists_created = []

    def mock_get_artists():
        artist = create_mock_artist()
        all_mock_artists_created.append(artist)
        return [artist]

    monkeypatch.setattr(global_collecting, "get_artists_collected", mock_get_artists)
    father_quib = iquib(1)
    quib = GraphicsFunctionQuib(
        args=tuple(),
        kwargs={},
        cache_behavior=CacheBehavior.ON,
        func=mock.Mock(),
        artists=[]
    )
    father_quib.add_child(quib)

    quib.get_value()
    father_quib.invalidate_and_redraw()

    assert len(all_mock_artists_created) == 2
    assert len(mock_axes.artists) == 1
