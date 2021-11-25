from unittest import mock

import pytest
from matplotlib.artist import Artist

from pyquibbler.graphics import global_collecting
from pyquibbler.quib.refactor.factory import create_quib


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


@pytest.mark.regression
def test_graphics_function_quib_doesnt_fail_on_removal_of_artists(create_quib_with_return_value, axes):
    quib = create_quib_with_return_value([1, 2, 3], allow_overriding=True)
    assert quib.get_value() == [1, 2, 3]
    axes.plot(quib)
    axes.cla()

    quib[0] = 10


def test_graphics_function_quib_copy_color(axes, create_quib_with_return_value):
    quib = create_quib_with_return_value([1., 2., 3.])
    plot_quib = axes.plot(quib)
    artist_color_upon_creation = plot_quib.get_value()[0].get_color()

    quib.invalidate_and_redraw_at_path()

    artist_color_after_redraw = plot_quib.get_value()[0].get_color()
    assert artist_color_upon_creation == artist_color_after_redraw
