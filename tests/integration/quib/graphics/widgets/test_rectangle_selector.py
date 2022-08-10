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
                                 roi, rectangle_selector, get_axes_middle, create_button_press_event,
                                 create_motion_notify_event, create_button_release_event):

    middle_x, middle_y = get_axes_middle()
    axes_x, axes_y, width, height = axes.bbox.bounds
    new_x = axes_x + width * .7
    new_y = axes_y + height * .7

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    original_num_artists = len(get_live_artists())

    with count_redraws(rectangle_selector) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_button_press_event(middle_x, middle_y)
        create_motion_notify_event(new_x, new_y)
        create_button_release_event(new_x, new_y)

    assert canvas_redraw_count.count == 1
    assert redraw_count.count == 1  # motion_notify

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == 1
    new_roi = roi.get_value()

    assert np.array_equal(np.round(new_roi, 4), [0.4, 1., 0.4, 1.])


@quibbler_image_comparison(baseline_images=['move_list'])
def test_rectangle_selector_list_extent_move(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                             roi_list, rectangle_selector_list_extents, get_axes_middle,
                                             create_button_press_event,
                                             create_motion_notify_event, create_button_release_event):

    middle_x, middle_y = get_axes_middle()
    axes_x, axes_y, width, height = axes.bbox.bounds
    new_x = axes_x + width * .7
    new_y = axes_y + height * .7

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    original_num_artists = len(get_live_artists())

    with count_redraws(rectangle_selector_list_extents) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_button_press_event(middle_x, middle_y)
        create_motion_notify_event(new_x, new_y)
        create_button_release_event(new_x, new_y)

    assert canvas_redraw_count.count == 1
    assert redraw_count.count == 1  # motion_notify

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == 1
    new_roi = [roi_item.get_value() for roi_item in roi_list]

    assert np.array_equal(np.round(new_roi, 4), [0.4, 1., 0.4, 1.])


def test_rectangle_selector_update(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                   roi, rectangle_selector):

    widget = rectangle_selector.get_value()
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.2, 0.2, 0.6, 0.6])

    roi[0] = 0.3
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.3, 0.2, 0.5, 0.6])


@pytest.mark.skip
@pytest.mark.benchmark()
def test_rectangle_selector_speed(axes,
                                  roi, rectangle_selector, get_axes_middle, create_button_press_event,
                                  create_motion_notify_event, create_button_release_event):
    import time

    middle_x, middle_y = get_axes_middle()
    axes_x, axes_y, width, height = axes.bbox.bounds
    new_x = axes_x + width * .7
    new_y = axes_y + height * .7

    start = time.time()

    for i in range(50):
        create_button_press_event(middle_x, middle_y)
        create_motion_notify_event(new_x, new_y)
        create_button_release_event(new_x, new_y)

        create_button_press_event(new_x, new_y)
        create_motion_notify_event(middle_x, middle_y)
        create_button_release_event(middle_x, middle_y)

    end = time.time()

    print()
    print(end - start)


def test_rectangle_selector_undo(axes,
                                 roi, rectangle_selector, get_axes_middle, create_button_press_event,
                                 create_motion_notify_event, create_button_release_event):

    middle_x, middle_y = get_axes_middle()
    axes_x, axes_y, width, height = axes.bbox.bounds
    new_x1 = axes_x + width * .6
    new_y1 = axes_y + height * .6
    new_x2 = axes_x + width * .7
    new_y2 = axes_y + height * .7

    assert roi.get_value()[0] == 0.2
    create_button_press_event(middle_x, middle_y)

    create_motion_notify_event(new_x1, new_y1)
    assert roi.get_value()[0] == 0.3

    create_motion_notify_event(new_x2, new_y2)
    assert roi.get_value()[0] == 0.4

    create_button_release_event(new_x2, new_y2)

    undo()
    assert roi.get_value()[0] == 0.2

    redo()
    assert roi.get_value()[0] == 0.4


def test_rectangle_selector_right_click_reset_to_default(axes,
                                                         roi, rectangle_selector, get_axes_middle,
                                                         create_button_press_event,
                                                         create_motion_notify_event, create_button_release_event):

    middle_x, middle_y = get_axes_middle()
    axes_x, axes_y, width, height = axes.bbox.bounds
    new_x1 = axes_x + width * .6
    new_y1 = axes_y + height * .6

    assert roi.get_value()[0] == 0.2
    create_button_press_event(middle_x, middle_y)

    create_motion_notify_event(new_x1, new_y1)
    create_button_release_event(new_x1, new_y1)
    assert roi.get_value()[0] == 0.3

    create_button_press_event(new_x1, new_y1, button=3)  # right-click
    create_button_release_event(new_x1, new_y1)
    assert roi.get_value()[0] == 0.2

    undo()
    assert roi.get_value()[0] == 0.3

    undo()
    assert roi.get_value()[0] == 0.2

    redo()
    assert roi.get_value()[0] == 0.3

    redo()
    assert roi.get_value()[0] == 0.2
