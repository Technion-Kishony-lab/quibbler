from matplotlib import pyplot as plt

from pyquibbler import iquib, undo, redo
from tests.integration.quib.graphics.widgets.utils import count_canvas_draws, count_redraws


def test_drag_along_shallow_slope(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 1)
    axes.set_ylim(-1, 1)

    marker_x = iquib(0.)
    marker_y = 0.1 * marker_x  # line with shallow slope
    plot_quib = axes.plot(marker_x, marker_y, marker='o')

    create_axes_mouse_press_move_release_events(((0, 0), (0.5, 0)))
    assert marker_x.get_value() == 0.496
