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
    assert marker_x.get_value() == 0.496


def test_drag_along_zero_slope(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 1)
    axes.set_ylim(-1, 1)

    marker_x = iquib(0.)
    marker_y = 0 * marker_x  # line with zero slope
    axes.plot(marker_x, marker_y, marker='o')

    create_axes_mouse_press_move_release_events(((0, 0), (0.5, 0)))
    assert marker_x.get_value() == 0.498


def test_drag_same_arg_binary_operator(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 4)
    axes.set_ylim(-1, 4)

    x = iquib(1.)
    xx = x + x
    axes.plot(xx, xx, marker='o')

    create_axes_mouse_press_move_release_events(((2, 2), (3, 3)))
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
