import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import widgets

from pyquibbler import iquib, undo, redo
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison, count_canvas_draws


@pytest.fixture
def roi():
    return iquib(np.array([.2, .8, 0.2, 0.8]))


@pytest.fixture
def rectangle_selector(roi, axes):
    selector = widgets.RectangleSelector(axes, extents=roi)
    plt.pause(0.1)
    return selector


@pytest.fixture
def roi_list():
    return [iquib(.2), iquib(.8), iquib(.2), iquib(.8)]


@pytest.fixture
def rectangle_selector_list_extents(roi_list, axes):
    selector = widgets.RectangleSelector(axes, extents=roi_list)
    plt.pause(0.1)
    return selector


@quibbler_image_comparison(baseline_images=['move'])
def test_rectangle_selector_move(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                 roi, rectangle_selector, create_axes_mouse_press_move_release_events):

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    original_num_artists = len(get_live_artists())

    with count_redraws(rectangle_selector) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6)])

    assert canvas_redraw_count.count == 1
    assert redraw_count.count == 1  # motion_notify

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == 1
    new_roi = roi.get_value()

    assert np.array_equal(new_roi, [0.3, 0.9, 0.3, 0.9])


@quibbler_image_comparison(baseline_images=['move_list'])
def test_rectangle_selector_list_extent_move(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                             roi_list, rectangle_selector_list_extents,
                                             create_axes_mouse_press_move_release_events):

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    original_num_artists = len(get_live_artists())

    with count_redraws(rectangle_selector_list_extents) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6)])

    assert canvas_redraw_count.count == 1
    assert redraw_count.count == 1  # motion_notify

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == 1
    new_roi = [roi_item.get_value() for roi_item in roi_list]

    assert np.array_equal(new_roi, [0.3, 0.9, 0.3, 0.9])


def test_rectangle_selector_update(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                   roi, rectangle_selector):

    widget = rectangle_selector.get_value()
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.2, 0.2, 0.6, 0.6])

    roi[0] = 0.3
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.3, 0.2, 0.5, 0.6])


@pytest.mark.benchmark()
def test_rectangle_selector_speed(benchmark, axes, roi, rectangle_selector,
                                  create_axes_mouse_press_move_release_events):
    def drag_n_drop():
        create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6)])
        create_axes_mouse_press_move_release_events([(0.6, 0.6), (0.5, 0.5)])

    benchmark(drag_n_drop)


def test_rectangle_selector_undo(axes, roi, rectangle_selector, create_axes_mouse_press_move_release_events):

    assert roi.get_value()[0] == 0.2

    create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6)], release=False)
    assert roi.get_value()[0] == 0.3

    create_axes_mouse_press_move_release_events([(0.6, 0.6), (0.65, 0.65)])
    assert roi.get_value()[0] == 0.35

    undo()
    assert roi.get_value()[0] == 0.2

    redo()
    assert roi.get_value()[0] == 0.35


def test_rectangle_selector_right_click_reset_to_default(axes, roi, rectangle_selector,
                                                         create_axes_mouse_press_move_release_events,
                                                         ):

    assert roi.get_value()[0] == 0.2
    create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6)])
    assert roi.get_value()[0] == 0.3

    create_axes_mouse_press_move_release_events([(0.6, 0.6)], button=3)
    assert roi.get_value()[0] == 0.2

    undo()
    assert roi.get_value()[0] == 0.3

    undo()
    assert roi.get_value()[0] == 0.2

    redo()
    assert roi.get_value()[0] == 0.3

    redo()
    assert roi.get_value()[0] == 0.2
