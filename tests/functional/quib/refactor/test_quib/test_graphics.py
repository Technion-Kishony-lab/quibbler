from unittest import mock

import pytest
from matplotlib.artist import Artist

from pyquibbler.graphics import global_collecting
from pyquibbler.quib.refactor.factory import create_quib
from pyquibbler.quib.refactor.iquib import iquib


@pytest.fixture()
def create_artist(mock_axes):

    def _create(*args):
        # We need this in order for artist to be tracked
        # TODO: is there a more canonical way?
        global_collecting.OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING = 1
        artist = Artist()
        artist.axes = mock_axes
        mock_axes.artists.append(artist)
        return artist

    return _create


@pytest.fixture()
def parent_quib():
    return create_quib(func=mock.Mock())


@pytest.fixture()
def graphics_quib(parent_quib, create_artist):
    return create_quib(
        func=create_artist,
        args=(parent_quib,)
    )


def test_quib_func_creates_graphics_returns_true_if_created_graphics(parent_quib, graphics_quib):
    assert graphics_quib.func_creates_graphics is False, "Sanity"
    graphics_quib.get_value()  # We should now know we create graphics

    assert graphics_quib.func_creates_graphics


def test_quib_func_creates_artist(parent_quib, graphics_quib, mock_axes):
    graphics_quib.get_value()

    assert len(mock_axes.artists) == 1


def test_quib_removes_artists_on_rerun(parent_quib, graphics_quib, mock_axes):
    graphics_quib.get_value()

    parent_quib.invalidate_and_redraw_at_path()

    assert len(mock_axes.artists) == 1
