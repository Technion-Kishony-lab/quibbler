import pytest
from unittest import mock

from pyquibbler.quib.graphics import graphics_function_quib
from pyquibbler.quib.graphics.vectorize import vectorize_graphics_function_quib


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
    axes.figure.canvas.supports_blit = False
    axes.artists = []
    return axes


@pytest.fixture()
def mock_artists_collector(mock_axes, monkeypatch):
    collector = MockArtistsCollector(mock_axes)
    monkeypatch.setattr(graphics_function_quib, "ArtistsCollector", lambda: collector) # TODO
    monkeypatch.setattr(vectorize_graphics_function_quib, "ArtistsCollector", lambda: collector)
    return collector
