from unittest import mock
from unittest.mock import Mock
from pytest import fixture

from pyquibbler.quib.graphics import overriding


@fixture()
def mock_artist(monkeypatch):
    return mock.Mock()


@fixture()
def override_global_artists_to_return_mock_artist(monkeypatch, mock_artist):
    def return_mock_artist_in_axes(*_):
        mock_artist.axes.artists = [mock_artist]
        return [mock_artist]

    monkeypatch.setattr(overriding, "get_global_artists_collected", return_mock_artist_in_axes)


@fixture
def assignment_template_mock():
    mock = Mock()
    mock.convert.return_value = object()
    return mock
