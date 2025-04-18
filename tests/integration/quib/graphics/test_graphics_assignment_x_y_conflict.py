import gc
import weakref
from functools import partial

import numpy as np

from ....conftest import plt_pause
from pyquibbler import iquib, quiby
from pyquibbler.quib.graphics.artist_wrapper import get_upstream_caller_quibs, get_creating_quib, get_all_setter_quibs
from tests.integration.quib.graphics.widgets.utils import count_canvas_draws, count_redraws, count_invalidations


def test_drag_along_shallow_slope(create_axes_mouse_press_move_release_events, axes):

    axes.set_xlim(-1, 1)
    axes.set_ylim(-1, 1)

    marker_x = iquib(0.)
    marker_y = 0.1 * marker_x  # line with shallow slope
    axes.plot(marker_x, marker_y, marker='o')

    create_axes_mouse_press_move_release_events(((0, 0), (0.5, 0)))
    assert marker_x.get_value() == 0.497


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


def test_drag_segment_single_value(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-2, 2)
    axes.set_ylim(-2, 2)

    a = iquib(0.)

    axes.plot([0, np.cos(a)], [0, np.sin(a)], 'o-')
    new_a = np.pi / 4
    create_axes_mouse_press_move_release_events(((0.5, 0.), (0.5*np.cos(new_a), 0.5*np.sin(new_a))))
    assert abs(a.get_value() - new_a) < 0.02


def test_drag_segment_two_values(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-2, 2)
    axes.set_ylim(-2, 2)

    x = iquib(1.)
    y = iquib(0.)

    axes.plot([0, x], [0, y], 'o-')

    create_axes_mouse_press_move_release_events(((0.5, 0.), (0.2, 0.2)))
    assert abs(x.get_value() - 0.4) < 0.02
    assert abs(y.get_value() - 0.4) < 0.02


def test_drag_parallel(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-2, 2)
    axes.set_ylim(-2, 2)

    x1 = iquib(0.)
    x2 = iquib(0.4)

    axes.plot([x1, x2], [0, 1], 'o-')

    create_axes_mouse_press_move_release_events(((0.1, 0.25), (0.3, 0.25)))
    assert abs(x1.get_value() - 0.2) < 0.02
    assert abs(x2.get_value() - 0.6) < 0.02


def test_drag_middle_tethered_line(create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(-2, 2)
    axes.set_ylim(-2, 2)

    x = iquib(1.)

    axes.plot([-x, x], [-1, 1], 'o-')

    create_axes_mouse_press_move_release_events(((0.5, 0.5), (0.4, 0.5)))

    assert abs(x.get_value() - 0.8) < 0.02


def test_drag_plot_created_in_quiby_func(axes, create_axes_mouse_press_move_release_events, live_artists):
    # create the figure
    axes.axis('square')
    axes.axis((-1., 10., -1., 10.))
    axes.set_xticks([])
    axes.set_yticks([])
    plt_pause(0.5)  # pause to allow axes to be resized. see assert below:
    assert np.abs(np.diff(axes.transData.transform((3, 3)) - axes.transData.transform((0, 0)))) < 1e-10
    creating_quib_ref = None

    @quiby(pass_quibs=True, is_graphics=True)
    def create_dot(a):
        nonlocal creating_quib_ref
        creating_quib = axes.plot(a * 3, a * 3, '.', markersize=15, color='c')
        creating_quib_ref = weakref.ref(creating_quib)

    a = iquib(0.)
    quiby_quib = create_dot(a)

    def get_and_check_artist():
        assert len(live_artists) == 1
        artist = live_artists.pop()
        assert get_upstream_caller_quibs(artist) == {quiby_quib}
        assert get_creating_quib(artist) is creating_quib_ref()
        return weakref.ref(artist)

    artist_ref_1 = get_and_check_artist()
    assert artist_ref_1() is not None

    creating_quib_ref1 = creating_quib_ref
    assert creating_quib_ref1() is not None

    with count_redraws(quiby_quib) as quiby_quib_redraw_count, \
            count_redraws(creating_quib_ref()) as ceating_quib_redraw_count, \
            count_invalidations(quiby_quib) as quiby_quib_invalidation_count, \
            count_invalidations(creating_quib_ref()) as creating_quib_invalidation_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
            create_axes_mouse_press_move_release_events(((0, 0), (0, 4), (0, 9)))

    assert creating_quib_ref1() is None
    gc.collect()  # needed to remove the circular reference: quib->func_call->graphics_collection->artist->quib
    assert artist_ref_1() is None

    artist_ref_2 = get_and_check_artist()

    assert quiby_quib_invalidation_count.count == 2
    assert quiby_quib_redraw_count.count == 2
    # print(creating_quib_invalidation_count.count, ceating_quib_redraw_count.count)
    assert canvas_redraw_count.count == 2
    assert abs(a.get_value() - 9 / 2 / 3) < 0.02


def test_vectorized_widgets(axes, create_axes_mouse_press_move_release_events):
    from matplotlib.widgets import RectangleSelector

    @partial(np.vectorize, signature='(4)->()', pass_quibs=True, is_graphics=True)
    def create_roi(roi):
        RectangleSelector(axes, extents=roi)

    axes.axis([0, 500, 0, 500])

    num_images = iquib(3)

    roi_default = iquib([[20, 100, 20, 100]], allow_overriding=False)

    rois = np.repeat(roi_default, num_images, axis=0).setp(allow_overriding=True)
    create_roi(rois)

    num_images.assign(2)

    create_axes_mouse_press_move_release_events(((60, 60), (100.5, 100.5)))
    assert np.array_equal(rois.get_value(), [[60, 140, 60, 140], [20, 100, 20, 100]])
