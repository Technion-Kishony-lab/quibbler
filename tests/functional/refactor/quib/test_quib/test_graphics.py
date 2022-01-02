from unittest import mock

import pytest
from matplotlib.artist import Artist

from pyquibbler.refactor.graphics import global_collecting
from pyquibbler.refactor.quib.factory import create_quib
from pyquibbler.refactor.quib.graphics import UpdateType, dragging


@pytest.fixture()
def parent_quib():
    return create_quib(func=mock.Mock())


@pytest.fixture()
def artist_graphics_quib(parent_quib, create_artist):
    return create_quib(
        func=create_artist,
        args=(parent_quib,)
    )


def test_quib_func_creates_graphics_returns_true_if_created_graphics(parent_quib, artist_graphics_quib):
    assert artist_graphics_quib.func_can_create_graphics is False, "Sanity"
    artist_graphics_quib.get_value()  # We should now know we create graphics

    assert artist_graphics_quib.func_can_create_graphics


def test_quib_func_creates_artist(parent_quib, artist_graphics_quib, mock_axes):
    artist_graphics_quib.get_value()

    assert len(mock_axes.artists) == 1


def test_quib_removes_artists_on_rerun(parent_quib, artist_graphics_quib, mock_axes):
    artist_graphics_quib.get_value()

    parent_quib.invalidate_and_redraw_at_path()

    assert len(mock_axes.artists) == 1


@pytest.mark.regression
def test_graphics_quib_doesnt_fail_on_removal_of_artists(create_quib_with_return_value, axes):
    quib = create_quib_with_return_value([1, 2, 3], allow_overriding=True)
    assert quib.get_value() == [1, 2, 3]
    axes.plot(quib)
    axes.cla()

    quib[0] = 10


def test_graphics_quib_copy_color(axes, create_quib_with_return_value):
    quib = create_quib_with_return_value([1., 2., 3.])
    plot_quib = axes.plot(quib)
    artist_color_upon_creation = plot_quib.get_value()[0].get_color()

    quib.invalidate_and_redraw_at_path()

    artist_color_after_redraw = plot_quib.get_value()[0].get_color()
    assert artist_color_upon_creation == artist_color_after_redraw


def test_graphics_quib_does_not_copy_color(axes, create_quib_with_return_value):
    parent_quib = create_quib_with_return_value([1., 2., 3.])
    color_quib = create_quib_with_return_value([1, 0, 0], allow_overriding=True)
    plot_quib = axes.plot(parent_quib, color=color_quib)
    artist_color_upon_creation = plot_quib.get_value()[0].get_color()

    color_quib[1] = 1

    artist_color_after_color_change = plot_quib.get_value()[0].get_color()
    assert artist_color_upon_creation == [1, 0, 0]
    assert artist_color_after_color_change == [1, 1, 0]


@pytest.mark.parametrize("update_type,should_have_called", [
    (UpdateType.DRAG, True),
    (UpdateType.DROP, False),
    (UpdateType.NEVER, False),
    (UpdateType.CENTRAL, False)
])
def test_graphics_quib_update_on_drag(update_type, should_have_called, quib, graphics_quib,
                                      create_quib_with_return_value):
    graphics_quib.set_redraw_update_type(update_type)
    with dragging():
        quib.invalidate_and_redraw_at_path([])

    assert len(graphics_quib.func.mock_calls) == (1 if should_have_called else 0)


def test_graphics_quib_update_on_drop(quib, graphics_quib):
    graphics_quib.set_redraw_update_type(UpdateType.DROP)

    quib.invalidate_and_redraw_at_path([])

    assert len(graphics_quib.func.mock_calls) == 1


@pytest.mark.parametrize("update_type", ["never", "central"])
def test_graphics_quib_which_should_never_update(update_type, quib, graphics_quib):
    graphics_quib.set_redraw_update_type(update_type)

    quib.invalidate_and_redraw_at_path([])

    assert len(graphics_quib.func.mock_calls) == 0
