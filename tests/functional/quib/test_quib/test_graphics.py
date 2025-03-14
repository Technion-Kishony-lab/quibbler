from unittest import mock

import numpy as np
import pytest
from matplotlib.axes import Axes

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
from pyquibbler.path import PathComponent
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics import GraphicsUpdateType, aggregate_redraw_mode
from pyquibbler.quib.graphics.redraw import start_dragging, end_dragging


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
    assert artist_graphics_quib.is_graphics_quib is False, "Sanity"
    artist_graphics_quib.get_value()  # We should now know we create graphics

    assert artist_graphics_quib.is_graphics_quib


def test_quib_func_creates_artist(parent_quib, artist_graphics_quib, mock_axes):
    artist_graphics_quib.get_value()

    assert len(mock_axes._children) == 1


def test_quib_removes_artists_on_rerun(parent_quib, artist_graphics_quib, mock_axes):
    artist_graphics_quib.get_value()
    parent_quib.handler.invalidate_and_aggregate_redraw_at_path()

    assert len(mock_axes._children) == 1


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

    quib.handler.invalidate_and_aggregate_redraw_at_path()

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


@pytest.mark.parametrize("graphics_update,should_have_called", [
    (GraphicsUpdateType.DRAG, True),
    (GraphicsUpdateType.DROP, False),
    (GraphicsUpdateType.NEVER, False),
    (GraphicsUpdateType.CENTRAL, False)
])
def test_graphics_quib_update_on_drag(graphics_update, should_have_called, quib, graphics_quib,
                                      create_quib_with_return_value):
    graphics_quib.graphics_update = graphics_update
    start_dragging(78)
    with aggregate_redraw_mode():
        quib.handler.invalidate_and_aggregate_redraw_at_path([])

    assert graphics_quib.func.call_count == (2 if should_have_called else 1)
    end_dragging(78)


def test_graphics_quib_update_on_drop(quib, graphics_quib):
    graphics_quib.graphics_update = GraphicsUpdateType.DROP

    quib.handler.invalidate_and_aggregate_redraw_at_path([])

    assert graphics_quib.func.call_count == 2


@pytest.mark.parametrize("graphics_update", ["never", "central"])
def test_graphics_quib_which_should_never_update(graphics_update, quib, graphics_quib):
    graphics_quib.graphics_update = graphics_update

    assert graphics_quib.func.call_count == 1, "sanity"

    quib.handler.invalidate_and_aggregate_redraw_at_path([])

    assert graphics_quib.func.call_count == 1


@pytest.fixture()
def replacing_func():
    mock_func = mock.Mock()
    mock_func.__name__ = "myfunc"
    add_definition_for_function(func=mock_func, func_definition=create_or_reuse_func_definition(is_graphics=True,
                                                                                                is_artist_setter=True),
                                )
    return mock_func


def test_replacing_graphics_function_quib(axes, create_quib_with_return_value, replacing_func):
    first_quib = create_quib_with_return_value(5)
    # Creating runs the quibs- it's also important to keep them as a local var so they don't get garbage collected
    # if they are the test will pass regardless
    _ = create_quib(
        func=replacing_func,
        args=(axes, first_quib),
        lazy=False
    )
    __ = create_quib(
        func=replacing_func,
        args=(axes,),
        lazy=False
    )

    first_quib.handler.invalidate_and_aggregate_redraw_at_path(path=[...])

    assert replacing_func.call_count == 2


@pytest.mark.regression
def test_replacing_graphics_function_quib_doesnt_remove_quib_after_invalidation_three_times(
        axes, create_quib_with_return_value, replacing_func
):
    first_quib = create_quib_with_return_value(5)
    path = [PathComponent(...)]
    # First time to create quib, attach to parent, attach to axes
    _ = create_quib(
        func=replacing_func,
        args=(axes, first_quib),
        lazy=False,
    )
    # Second time to potentially remove from axes (this was the bug)
    first_quib.handler.invalidate_and_aggregate_redraw_at_path(path=path)

    # Third time to make sure we DID stay attached to our parent
    first_quib.handler.invalidate_and_aggregate_redraw_at_path(path=path)

    assert replacing_func.call_count == 3


@pytest.mark.regression
def test_replacing_graphics_function_quib_is_removed_after_call_with_no_quibs(create_quib_with_return_value, axes):
    quib = create_quib_with_return_value('bad title', allow_overriding=True)
    axes.set_title(quib)

    assert axes.get_title() == quib.get_value(), "sanity"

    axes.set_title('good title')
    assert axes.get_title() == 'good title', "sanity"

    quib.assign('another bad title')

    # this was the bug:
    assert axes.get_title() == 'good title'


@pytest.mark.regression
def test_inverse_assignment_from_axis_lim_scalar(create_quib_with_return_value, axes):
    quib = create_quib_with_return_value(2., allow_overriding=True)
    axes.set_xlim([0., quib])

    axes.set_xlim(np.array([1., 3.]), called_from_drag_pan=True)
    assert quib.get_value() == 3.


@pytest.mark.regression
def test_inverse_assignment_from_axis_lim_vector(create_quib_with_return_value, axes):
    quib = create_quib_with_return_value(np.array([0., 2.]), allow_overriding=True)
    axes.set_xlim(quib)

    axes.set_xlim(np.array([1., 3.]), called_from_drag_pan=True)
    assert np.array_equal(quib.get_value(), [1., 3.])


@pytest.mark.regression
def test_inverse_assignment_is_not_invoked_when_axis_lim_is_set_manually(create_quib_with_return_value, axes):
    quib = create_quib_with_return_value(2., allow_overriding=True)
    axes.set_xlim([0., quib])

    axes.set_xlim([1., 3.])
    assert quib.get_value() == 2.
