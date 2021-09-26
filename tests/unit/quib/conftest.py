from unittest import mock

import pytest

from pyquibbler.quib.graphics import overriding


@pytest.fixture()
def mock_artist(monkeypatch):
    return mock.Mock()


@pytest.fixture()
def override_global_artists_to_return_mock_artist(monkeypatch, mock_artist):
    def return_mock_artist_in_axes(*_):
        mock_artist.axes.artists = [mock_artist]
        return [mock_artist]

    monkeypatch.setattr(overriding, "get_global_artists_collected", return_mock_artist_in_axes)