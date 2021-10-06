from unittest import mock

import numpy as np
import pytest
from matplotlib.axes import Axes

from pyquibbler import iquib
from pyquibbler.quib.graphics import GraphicsFunctionQuib
from pyquibbler.quib.graphics.event_handling.graphics_reverse_assigner import reverse_assign_drawing_func


@pytest.fixture
def mock_plot():
    func = mock.Mock()
    func.__qualname__ = 'Axes.plot'
    return func


def create_mock_pick_event_and_mouse_event(indices, x_data, y_data):
    mouse_event = mock.Mock()
    mouse_event.xdata = x_data
    mouse_event.ydata = y_data

    pick_event = mock.Mock()
    pick_event.ind = indices

    return pick_event, mouse_event


def test_plot_reverse_assigner_happy_flow(mock_plot):
    q = iquib(np.array([1, 2, 3]))
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(0, 10, 20)

    reverse_assign_drawing_func(
        drawing_func=mock_plot,
        args=(None, q),
        mouse_event=mouse_event,
        pick_event=pick_event
    )

    assert np.array_equal(q.get_value(), [20, 2, 3])


@pytest.mark.parametrize("indices,xdata,ydata,args,quib_index,expected_value", [
    (0, 100, 50, (iquib([0, 0, 0]),), 0, [50, 0, 0]),
    (0, 100, 50, (iquib([0, 0, 0]), None), 0, [100, 0, 0]),
    (0, 100, 50, (iquib([0, 0, 0]), None, "i_is_fmt"), 0, [100, 0, 0]),
    (0, 100, 50, (None, None, "i_is_fmt", iquib([0, 0, 0]), None), 3, [100, 0, 0]),
    (0, 100, 50, (None, None, "i_is_fmt", None, iquib([0, 0, 0])), 4, [50, 0, 0]),
    (0, 100, 50, (None, None, None, iquib([0, 0, 0])), 3, [50, 0, 0])
], ids=["ydata: one arg", "xdata: two args", "xdata: three args", "xdata: second group after fmt",
        "ydata: second group after fmt", "ydata: no fmt"])
def test_plot_reverse_assigner(mock_plot, indices, xdata, ydata, args, quib_index, expected_value):
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(indices, xdata, ydata)

    reverse_assign_drawing_func(
        drawing_func=mock_plot,
        args=(None, *args),
        mouse_event=mouse_event,
        pick_event=pick_event
    )

    assert np.array_equal(args[quib_index].get_value(), expected_value)
