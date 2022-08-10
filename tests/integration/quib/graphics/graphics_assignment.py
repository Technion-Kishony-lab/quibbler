from matplotlib import pyplot as plt

from pyquibbler import iquib, undo, redo
from tests.integration.quib.graphics.widgets.utils import count_canvas_draws, count_redraws


def test_drag_right_click_and_undo(create_button_press_event, create_motion_notify_event, create_button_release_event,
                    axes, get_live_artists):

    max_xlim = 20
    axes.set_xlim([0, max_xlim])
    axes.set_ylim([0, 1])

    marker_x = iquib(15)
    plot_quib = axes.plot(marker_x, 0, markerfacecolor='k', marker='^', markersize=30, pickradius=30)

    x_origin, y_origin, width, height = axes.bbox.bounds
    marker_y = y_origin + 5
    x_15 = width * (15 / max_xlim) + x_origin
    x_10 = width * (10 / max_xlim) + x_origin
    x_5 = width * (5 / max_xlim) + x_origin

    with count_redraws(plot_quib) as quib_redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_button_press_event(x_15, marker_y)
        create_motion_notify_event(x_10, marker_y)
        assert marker_x.get_value() == 10

        create_motion_notify_event(x_5, marker_y)
        assert marker_x.get_value() == 5

        create_button_release_event(x_5, marker_y)

        create_button_press_event(x_5, marker_y, button=3)  # right click (reset to default)
        create_button_release_event(x_5, marker_y, button=3)
        assert marker_x.get_value() == 15

        undo()
        assert marker_x.get_value() == 5

        undo()
        assert marker_x.get_value() == 15

    assert canvas_redraw_count.count == 5  # 2 x motion + reset + 2 x undo
    assert quib_redraw_count.count == 5


def test_drag_xy_undo(create_button_press_event, create_motion_notify_event, create_button_release_event,
                      axes, get_live_artists):

    max_lim = 20
    axes.set_xlim(0, max_lim)
    axes.set_ylim(0, max_lim)

    xy = iquib([15, 15])
    x, y = xy
    plot_quib = axes.plot(x, y, markerfacecolor='k', marker='o')

    x_origin, y_origin, width, height = axes.bbox.bounds
    x_15 = width * (15 / max_lim) + x_origin
    x_10 = width * (10 / max_lim) + x_origin
    x_5 = width * (5 / max_lim) + x_origin
    y_15 = height * (15 / max_lim) + y_origin
    y_10 = height * (10 / max_lim) + y_origin
    y_5 = height * (5 / max_lim) + y_origin

    create_button_press_event(x_15, y_15)
    create_motion_notify_event(x_10, y_10)
    create_motion_notify_event(x_5, y_5)
    create_button_release_event(x_5, y_5)

    assert xy.get_value() == [5, 5]

    undo()
    assert xy.get_value() == [15, 15]

    redo()
    assert xy.get_value() == [5, 5]
