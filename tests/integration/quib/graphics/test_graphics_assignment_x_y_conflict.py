from matplotlib import pyplot as plt
import pytest

from pyquibbler import iquib, undo, redo
from tests.integration.quib.graphics.widgets.utils import count_canvas_draws, count_redraws


def test_drag_along_shallow_slope(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 1)
    axes.set_ylim(-1, 1)

    marker_x = iquib(0.)
    marker_y = 0.1 * marker_x  # line with shallow slope
    axes.plot(marker_x, marker_y, marker='o')

    create_axes_mouse_press_move_release_events(((0, 0), (0.5, 0)))
    assert marker_x.get_value() == 0.494


def test_drag_along_zero_slope(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 1)
    axes.set_ylim(-1, 1)

    marker_x = iquib(0.)
    marker_y = 0 * marker_x  # line with zero slope
    axes.plot(marker_x, marker_y, marker='o')

    create_axes_mouse_press_move_release_events(((0, 0), (0.5, 0)))
    assert marker_x.get_value() == 0.497


def test_drag_same_arg_binary_operator(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 4)
    axes.set_ylim(-1, 4)

    x = iquib(1.)
    xx = x + x
    axes.plot(xx, xx, marker='o')

    create_axes_mouse_press_move_release_events(((2, 2), (3, 3)))
    assert abs(xx.get_value() - 3) < 0.01


def test_drag_same_arg_binary_operator_single_axis(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 4)
    axes.set_ylim(-1, 4)

    x = iquib(1.)
    xx = x + x
    axes.plot(xx, 1, marker='o')

    create_axes_mouse_press_move_release_events(((2, 1), (3, 1)))
    assert abs(xx.get_value() - 3) < 0.01


# stong non-linear functions with binary operators are not currently solved correctly.
# See "Improve results with numeric solution" in graphics_inverse_assignment
@pytest.mark.skip
def test_drag_same_arg_binary_operator_non_linear(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-1, 4)
    axes.set_ylim(-1, 4)

    x = iquib(1.)
    x4 = x ** 2
    xx = x + x4
    axes.plot(xx, xx, marker='o')

    create_axes_mouse_press_move_release_events(((2, 2), (3, 3)))
    assert abs(xx.get_value() - 3) < 0.01


def test_prevent_drag_causing_exception(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-1, 4)
    axes.set_ylim(-1, 4)

    data = iquib([0, 1, 2])
    index = iquib(0)

    axes.plot(index, 0, marker='o')
    axes.plot(data[index], 1, marker='o')  # exception for x > 2

    create_axes_mouse_press_move_release_events(((0, 0), (1, 0)), release=False)
    assert index.get_value() == 1

    create_axes_mouse_press_move_release_events(((1, 0), (2, 0)), press=False, release=False)
    assert index.get_value() == 2

    create_axes_mouse_press_move_release_events(((2, 0), (3, 0)), press=False, release=False)
    assert index.get_value() == 2  # drag is prevented

    create_axes_mouse_press_move_release_events(((2, 0),), press=False)


def test_drag_segment(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-1, 4)
    axes.set_ylim(-1, 4)

    x = iquib(0.5)

    axes.plot([x, x], [1 - x, 0], 'o-')

    create_axes_mouse_press_move_release_events(((0.5, 0.2), (0.3, 0.2)))
    assert x.get_value() == 0.3
