from matplotlib import pyplot as plt

from pyquibbler import iquib, undo, redo
from tests.integration.quib.graphics.widgets.utils import count_canvas_draws, count_redraws


def test_drag_right_click_and_undo(create_axes_mouse_press_move_release_events, axes, get_live_artists):

    max_xlim = 20
    axes.set_xlim([0, max_xlim])
    axes.set_ylim([0, 1])

    marker_x = iquib(15)
    plot_quib = axes.plot(marker_x, 0, markerfacecolor='k', marker='^', markersize=30, pickradius=30)

    with count_redraws(plot_quib) as quib_redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_axes_mouse_press_move_release_events(((15, 0), (10, 0)))
        assert marker_x.get_value() == 10

        create_axes_mouse_press_move_release_events(((10, 0), (5, 0)))
        assert marker_x.get_value() == 5

        create_axes_mouse_press_move_release_events(((5, 0),))

        # right click (reset to default)
        create_axes_mouse_press_move_release_events(((5, 0),), button=3)
        assert marker_x.get_value() == 15

        undo()
        assert marker_x.get_value() == 5

        undo()
        assert marker_x.get_value() == 10

    assert canvas_redraw_count.count == 5  # 2 x motion + reset + 2 x undo
    assert quib_redraw_count.count == 5


def test_drag_xy_undo(axes, create_axes_mouse_press_move_release_events, get_live_artists):

    max_lim = 20
    axes.set_xlim(0, max_lim)
    axes.set_ylim(0, max_lim)

    xy = iquib([15, 15])
    x, y = xy
    axes.plot(x, y, markerfacecolor='k', marker='o')

    create_axes_mouse_press_move_release_events(((15, 15), (10, 10), (5, 5)))

    assert xy.get_value() == [5, 5]

    undo()
    assert xy.get_value() == [15, 15]

    redo()
    assert xy.get_value() == [5, 5]


def test_drag_multi_plot(axes, create_axes_mouse_press_move_release_events):
    x1 = iquib([10, 20, 30])
    x2 = iquib([40, 50, 60])
    axes.plot([x1, x2])
    create_axes_mouse_press_move_release_events(((0, 20), (0, 23)))

    assert x1.get_value() == [10, 23, 30]
    assert x2.get_value() == [40, 50, 60]


def testy_drag_axvline(axes, create_axes_mouse_press_move_release_events):
    x = iquib(10)
    axes.axis([0, 100, 0, 100])
    axes.axvline(x)

    create_axes_mouse_press_move_release_events(((10, 2), (23, 4)))

    assert x.get_value() == 23


def testy_drag_scatter_with_mouse_off_point(axes, create_axes_mouse_press_move_release_events):
    x = iquib([10, 20, 30])
    y = iquib([10, 20, 30])
    axes.axis([0, 100, 0, 100])
    axes.scatter(x, y)

    create_axes_mouse_press_move_release_events(((9, 10), (15, 5)))

    assert x.get_value() == [16, 20, 30]
    assert y.get_value() == [5, 20, 30]


def test_keep_fixed_mouse_distance_from_picked_point(axes, create_axes_mouse_press_move_release_events):
    x = iquib([10.1, 30])
    axes.plot(x, x, 'o')
    create_axes_mouse_press_move_release_events(((10, 10), (16, 16)))

    assert x.get_value() == [16.1, 30]


def test_only_pick_single_point(axes, create_axes_mouse_press_move_release_events):
    x = iquib([10.1, 10.1, 30])
    axes.plot(x, x, 'o')
    create_axes_mouse_press_move_release_events(((10, 10), (16, 16)))

    assert x.get_value() == [16.1, 10.1, 30]


def test_pick_segment(axes, create_axes_mouse_press_move_release_events):
    x = iquib([1, 10, 20])
    y = iquib([1, 10, 20])
    axes.plot(x, y, 'o-')
    dx = 2
    dy = 3
    create_axes_mouse_press_move_release_events(((5, 5), (5+dx, 5+dy)))

    assert x.get_value() == [1+dx, 10+dx, 20]
    assert y.get_value() == [1+dy, 10+dy, 20]


def test_drag_one_object_to_affect_another_1d(axes, create_axes_mouse_press_move_release_events):
    x = iquib(5.)
    dx = x - x
    axes.axis([-10, 10, -10, 10])
    axes.plot(dx, 0, 'o')
    create_axes_mouse_press_move_release_events(((0, 0), (2, 0)))

    assert abs(x.get_value() - 7) < 0.04


def test_drag_one_object_to_affect_another_2d(axes, create_axes_mouse_press_move_release_events):
    x = iquib(5.)
    y = iquib(5.)
    dx = x - x
    dy = y - y
    axes.axis([-10, 10, -10, 10])
    axes.plot(dx, dy, 'o')
    create_axes_mouse_press_move_release_events(((0, 0), (2, 2)))

    assert abs(x.get_value() - 7) < 0.04
    assert abs(y.get_value() - 7) < 0.04

