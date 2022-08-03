import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import widgets

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison


@pytest.fixture
def roi():
    return iquib(np.array([.2, .8, 0.2, 0.8]))


@pytest.fixture
def rectangle_selector(roi, axes):
    selector = widgets.RectangleSelector(axes, extents=roi)
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

    with count_redraws(rectangle_selector) as redraw_count:
        create_button_press_event(middle_x, middle_y)
        create_motion_notify_event(new_x, new_y)
        create_button_release_event(new_x, new_y)

    assert redraw_count.count == 2  # motion_notify and button_release

    assert len(axes.patches) == 1
    assert len(axes.lines) == 3
    assert len(get_live_artists()) == original_num_artists

    assert len(get_live_widgets()) == 1
    new_roi = roi.get_value()

    assert np.array_equal(np.round(new_roi, 4), [0.4, 1., 0.4, 1.])


def test_rectangle_selector_update(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                   roi, rectangle_selector):

    widget = rectangle_selector.get_value()
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.2, 0.2, 0.6, 0.6])

    roi[0] = 0.3
    bbox = widget._rect_bbox
    assert np.array_equal(np.round(bbox, 4), [0.3, 0.2, 0.5, 0.6])
