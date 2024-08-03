import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import widgets

from conftest import get_axes, create_mouse_press_move_release_events
from pyquibbler import iquib, undo, redo
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison, count_canvas_draws


@pytest.fixture
def roi():
    return iquib(np.array([.2, .8, 0.2, 0.8]))


def create_rectangle_selector(ax, extents):
    selector = widgets.RectangleSelector(ax, extents=extents)
    plt.pause(0.1)
    return selector


@pytest.fixture
def roi_list():
    return [iquib(.2), iquib(.8), iquib(.2), iquib(.8)]


@quibbler_image_comparison(baseline_images=['move'])
def test_rectangle_selector_move(get_only_live_widget, get_live_artists, get_live_widgets, roi):
    axes = get_axes()
    rectangle_selector = create_rectangle_selector(axes, roi)
    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    original_num_artists = len(get_live_artists())
    original_num_widgets = len(get_live_widgets())

    with count_redraws(rectangle_selector) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_mouse_press_move_release_events(axes, [(0.5, 0.5), (0.6, 0.6)])

    assert canvas_redraw_count.count == 1
    assert redraw_count.count == 1  # motion_notify

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == original_num_widgets
    new_roi = roi.get_value()

    assert np.array_equal(np.round(new_roi, 2), [0.3, 0.9, 0.3, 0.9])


@quibbler_image_comparison(baseline_images=['move_list'])
def test_rectangle_selector_list_extent_move(get_only_live_widget, get_live_artists, get_live_widgets, roi_list):
    axes = get_axes()
    rectangle_selector_list_extents = create_rectangle_selector(axes, roi_list)
    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    original_num_artists = len(get_live_artists())

    with count_redraws(rectangle_selector_list_extents) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_mouse_press_move_release_events(axes, [(0.5, 0.5), (0.6, 0.6)])

    assert canvas_redraw_count.count == 1
    assert redraw_count.count == 1  # motion_notify

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == 1
    new_roi = [roi_item.get_value() for roi_item in roi_list]

    assert np.array_equal(np.round(new_roi, 2), [0.3, 0.9, 0.3, 0.9])


def test_rectangle_selector_update(axes, get_only_live_widget, get_live_artists, get_live_widgets, roi):
    rectangle_selector = create_rectangle_selector(axes, roi)
    widget = rectangle_selector.get_value()
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.2, 0.2, 0.6, 0.6])

    roi[0] = 0.3
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.3, 0.2, 0.5, 0.6])


@pytest.mark.benchmark()
def test_rectangle_selector_speed(benchmark, axes, roi):
    def drag_n_drop():
        create_mouse_press_move_release_events(axes, [(0.5, 0.5), (0.6, 0.6)])
        create_mouse_press_move_release_events(axes, [(0.6, 0.6), (0.5, 0.5)])

    rectangle_selector = create_rectangle_selector(axes, roi)
    benchmark(drag_n_drop)


def test_rectangle_selector_undo(axes, roi):
    rectangle_selector = create_rectangle_selector(axes, roi)
    assert roi.get_value()[0] == 0.2

    create_mouse_press_move_release_events(axes, [(0.5, 0.5), (0.6, 0.6)], release=False)
    assert roi.get_value()[0] == 0.3

    create_mouse_press_move_release_events(axes, [(0.6, 0.6), (0.65, 0.65)])
    assert roi.get_value()[0] == 0.35

    undo()
    assert roi.get_value()[0] == 0.2

    redo()
    assert roi.get_value()[0] == 0.35


def test_rectangle_selector_right_click_reset_to_default(roi):
    axes = get_axes()
    rectangle_selector = create_rectangle_selector(axes, roi)
    assert roi.get_value()[0] == 0.2
    create_mouse_press_move_release_events(axes, [(0.5, 0.5), (0.6, 0.6)])
    assert roi.get_value()[0] == 0.3

    create_mouse_press_move_release_events(axes, [(0.6, 0.6)], button=3)
    assert roi.get_value()[0] == 0.2

    undo()
    assert roi.get_value()[0] == 0.3

    undo()
    assert roi.get_value()[0] == 0.2

    redo()
    assert roi.get_value()[0] == 0.3

    redo()
    assert roi.get_value()[0] == 0.2
