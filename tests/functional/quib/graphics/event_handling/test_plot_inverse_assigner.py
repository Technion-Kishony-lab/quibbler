from unittest import mock

import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.quib.graphics.event_handling.graphics_inverse_assigner import inverse_assign_drawing_func
from datetime import datetime
from matplotlib.dates import date2num

@pytest.fixture
def mock_plot():
    func = mock.Mock()
    func.__qualname__ = 'Axes.plot'
    return func


def create_mock_pick_event_and_mouse_event(indices, x_data, y_data, artist_index):
    mouse_event = mock.Mock()
    mouse_event.xdata = x_data
    mouse_event.ydata = y_data

    pick_event = mock.Mock()
    pick_event.ind = indices
    pick_event.artist._index_in_plot = artist_index
    pick_event.artist.axes.get_xlim = mock.Mock(return_value=[0, 100])
    pick_event.artist.axes.get_ylim = mock.Mock(return_value=[0, 100])

    return pick_event, mouse_event


def test_plot_inverse_assigner_happy_flow(mock_plot):
    q = iquib(np.array([1, 2, 3]))
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event([0], 10, 20, 0)

    inverse_assign_drawing_func(
        drawing_func=mock_plot,
        args=(None, q),
        mouse_event=mouse_event,
        pick_event=pick_event
    )

    assert np.array_equal(q.get_value(), [20, 2, 3])


date_array = np.array([datetime.strptime('2019-01-01','%Y-%m-%d'), datetime.strptime('2021-01-01','%Y-%m-%d')])
new_date = datetime.strptime('2019-01-02','%Y-%m-%d')


@pytest.mark.parametrize("indices,artist_index,xdata,ydata,args,quib_index,expected_value", [
    ([0], 0, 100, date2num(new_date), (iquib(date_array),), 0, np.array([new_date, date_array[1]])),
], ids=[
    "ydata: one arg datetime",
])
def test_plot_inverse_assigner(mock_plot, indices, artist_index, xdata, ydata, args, quib_index, expected_value):
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(indices, xdata, ydata, artist_index)
 
    inverse_assign_drawing_func(
        drawing_func=mock_plot,
        args=(None, *args),
        mouse_event=mouse_event,
        pick_event=pick_event
    )

    if isinstance(quib_index, int):
        quib_index = [quib_index]
        expected_value = [expected_value]
    for index, expected in zip(quib_index, expected_value):
        assert np.array_equal(args[index].get_value(), expected)


@pytest.mark.parametrize("indices,artist_index,xdata,ydata,args,arg_index,list_index,expected_value", [
    ([0], 0, 100, 50, ([iquib(0), 0, 0],), 0, 0, 50),
], ids=[
    "ydata: one list arg",
])
def test_plot_inverse_assigner_of_list_arg(mock_plot, indices, artist_index, xdata, ydata, args, arg_index,
                                           list_index, expected_value):
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(indices, xdata, ydata, artist_index)

    inverse_assign_drawing_func(
        drawing_func=mock_plot,
        args=(None, *args),
        mouse_event=mouse_event,
        pick_event=pick_event
    )

    assert np.array_equal(args[arg_index][list_index].get_value(), expected_value)
