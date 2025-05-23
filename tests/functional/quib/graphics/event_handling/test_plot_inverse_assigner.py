from dataclasses import dataclass
from unittest import mock

import numpy as np
import pytest
from matplotlib.backend_bases import MouseButton

from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.quib.graphics.event_handling.enhance_pick_event import EnhancedPickEvent, \
    EnhancedPickEventWithFuncArgsKwargs
from pyquibbler.quib.graphics.event_handling.graphics_inverse_assigner import inverse_assign_drawing_func
from datetime import datetime
from matplotlib.dates import date2num

from pyquibbler.quib.specialized_functions.iquib import create_iquib

iquib = create_iquib

@dataclass
class TempEnhancedPickEvent(EnhancedPickEventWithFuncArgsKwargs):

    @classmethod
    def from_pick_event_and_func_args_kwargs(cls, pick_event, func_args_kwargs):
        obj = cls.from_pick_event(pick_event)
        obj.func_args_kwargs = func_args_kwargs
        return obj


@pytest.fixture
def mock_plot():
    func = mock.Mock()
    func.__qualname__ = 'Axes.plot'
    return func


@pytest.fixture
def mock_scatter():
    func = mock.Mock()
    func.__qualname__ = 'Axes.scatter'
    return func


def create_mock_axes():
    pixels_to_data = 10
    ax = mock.Mock()
    ax.get_xlim = mock.Mock(return_value=[0, 100])
    ax.get_ylim = mock.Mock(return_value=[0, 100])
    ax.transData = mock.Mock()
    def transform(x):
        # check if datetime:
        if isinstance(x, np.ndarray):
            return np.array([transform(xi) for xi in x])
        if isinstance(x, datetime):
            x = date2num(x)
        return x * pixels_to_data

    ax.transData.transform = transform
    inverted_function = mock.Mock()
    inverted_function.transform = lambda x: x / pixels_to_data
    ax.transData.inverted = mock.Mock(return_value=inverted_function)
    return ax


def create_mock_pick_event_and_mouse_event(indices, x_data, y_data, artist_index):
    ax = create_mock_axes()
    mouse_event = mock.Mock()
    mouse_event.xdata = x_data
    mouse_event.ydata = y_data
    mouse_event.x = ax.transData.transform(x_data)
    mouse_event.y = ax.transData.transform(y_data)

    pick_event = mock.Mock()
    pick_event.ind = indices
    pick_event.artist._index_in_plot = artist_index
    pick_event.artist.axes = ax
    pick_event.mouseevent = mouse_event

    return pick_event, mouse_event


def create_mock_pick_event_right_click(indices, artist_index):
    pick_event = mock.Mock()
    pick_event.ind = indices
    pick_event.artist._index_in_plot = artist_index
    pick_event.mouseevent = mock.Mock()
    pick_event.mouseevent.button = MouseButton.RIGHT

    return pick_event


def test_plot_inverse_assigner_happy_flow(mock_plot):
    q = iquib(np.array([1, 2, 3]))
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event([0], 10, 20, 0)

    inverse_assign_drawing_func(
        enhanced_pick_event=TempEnhancedPickEvent.from_pick_event_and_func_args_kwargs(
            pick_event, FuncArgsKwargs(mock_plot, (None, q), {})),
        mouse_event=mouse_event,
    )

    assert np.array_equal(q.get_value(), [20, 2, 3])


date_array = np.array([datetime.strptime('2019-01-01','%Y-%m-%d'), datetime.strptime('2021-01-01','%Y-%m-%d')])
new_date = datetime.strptime('2019-01-02','%Y-%m-%d')


@pytest.mark.parametrize("indices,artist_index,xdata,ydata,args,quib_index,expected_value,tolerance", [
    ([0], 0, 100, 50, (iquib([0, 0, 0]),), 0, [50, 0, 0], None),
    ([0], 0, 100, 50, (iquib([0, 0, 0]), 'fmt'), 0, [50, 0, 0], None),
    ([0], 0, 100, 50, (iquib([0, 0, 0]), iquib('fmt')), 0, [50, 0, 0], None),
    ([0], 0, 100., 50.123456, (iquib([0., 0., 0.]),), 0, [50.123456, 0, 0], None),
    ([0], 0, 100., 50.123456, (iquib([0., 0., 0.]),), 0, [50.1, 0, 0], 1000),
    ([0], 0, 100., 50.123456, (iquib([0., 0., 0.]),), 0, [50.0, 0, 0], 100),
    ([0], 0, 100., 50.123456, (iquib([0., 0., 0.]),), 0, [50.0, 0, 0], 10),
    ([0], 0, 100, date2num(new_date), (iquib(date_array),), 0, np.array([new_date, date_array[1]]), None),
    ([0], 0, 100, 50, (iquib([0, 0, 0]), None), 0, [100, 0, 0], None),
    ([0], 0, 100, 50, (iquib([0, 0, 0]), None, "fmt"), 0, [100, 0, 0], None),
    ([0], 0, 100, 50, (iquib([0, 0, 0]), None, iquib("fmt")), 0, [100, 0, 0], None),
    ([0], 3, 100, 50, (np.zeros((2, 3)), np.zeros((2, 1)), "fmt", iquib([0, 0, 0]), None), 3, [100, 0, 0], None),
    ([0], 3, 100, 50, (np.zeros((2, 3)), np.zeros((2, 1)), "fmt", [0, 1, 2], iquib([0, 0, 0])), 4, [50, 0, 0], None),
    ([0], 1, 100, 50, (0, 0, [1, 2, 3], iquib([0, 0, 0])), 3, [50, 0, 0], None),
    ([1, 2], 0, 55, 66, (iquib([0, 0, 0]), iquib([0, 0, 0])), [0, 1], ([0, 55, 55], [0, 66, 66]), None),
    ([0], 0, 1, 2, (iquib(100), iquib(200)), [0, 1], (1, 2), None),
    ([1], 0, 4, 5, (iquib([[1], [2], [3]]),), 0, [[1], [5], [3]], None),
    ([1], 1, 8, 10, ([[4, 5], [6, 7], [8, 9]], iquib([[1], [2], [3]]),), 1, [[1], [10], [3]], None),
    ([1], 2, 8, 10, ([[4, 5], [6, 7], [8, 9]], [[1], [2], [3]], [[4, 5], [6, 7], [8, 9]], iquib([[1], [2], [3]]),), 3, [[1], [10], [3]], None),
], ids=[
    "ydata: one arg",
    "ydata: y, str",
    "ydata: y, iquib(str)",
    "ydata: one arg, tolerance none",
    "ydata: one arg, tolerance 1000",
    "ydata: one arg, tolerance 100",
    "ydata: one arg, tolerance 10",
    "ydata: one arg datetime",
    "xdata: two args",
    "xdata: three args",
    "xdata: three args, iquib(str)",
    "xdata: second group after fmt",
    "ydata: second group after fmt",
    "ydata: no fmt",
    "xdata&ydata: two marker drag",
    "xdata&ydata: input number",
    "ydata: input 2d array",
    "ydata: input nx1 array, broadcasting",
    "ydata: multiple x-y pairs",
])
def test_plot_inverse_assigner(mock_plot, indices, artist_index, xdata, ydata, args, quib_index, expected_value, tolerance):
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(indices, xdata, ydata, artist_index)

    with GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.temporary_set(tolerance):
        inverse_assign_drawing_func(
            enhanced_pick_event=TempEnhancedPickEvent.from_pick_event_and_func_args_kwargs(
                pick_event, FuncArgsKwargs(mock_plot, (None, *args), {})),
            mouse_event=mouse_event,
        )

    if isinstance(quib_index, int):
        quib_index = [quib_index]
        expected_value = [expected_value]
    for index, expected in zip(quib_index, expected_value):
        print(args[index].get_value())
        print(expected)
        assert np.array_equal(args[index].get_value(), expected)


@pytest.mark.graphics_driven_assignment_resolution(1000)
@pytest.mark.parametrize("indices,artist_index,xdata,ydata,args,arg_index,list_index,expected_value", [
    ([0], 0, 100, 50, ([iquib(0), 0, 0],), 0, 0, 50),
], ids=[
    "ydata: one list arg",
])
def test_plot_inverse_assigner_of_list_arg(mock_plot, indices, artist_index, xdata, ydata, args, arg_index,
                                           list_index, expected_value):
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(indices, xdata, ydata, artist_index)

    inverse_assign_drawing_func(
        enhanced_pick_event=TempEnhancedPickEvent.from_pick_event_and_func_args_kwargs(
            pick_event=pick_event,
            func_args_kwargs=FuncArgsKwargs(mock_plot, (None, *args), {})),
        mouse_event=mouse_event,
    )

    assert np.array_equal(args[arg_index][list_index].get_value(), expected_value)


def test_plot_inverse_assigner_removal(mock_plot):
    pick_event = create_mock_pick_event_right_click([1], 0)

    y = iquib([1, 2, 3])
    y[1] = 4

    assert y.get_value() == [1, 4, 3], "sanity"

    inverse_assign_drawing_func(
        enhanced_pick_event=TempEnhancedPickEvent.from_pick_event_and_func_args_kwargs(
            pick_event=pick_event,
            func_args_kwargs=FuncArgsKwargs(mock_plot, (None, y), {})),
        mouse_event=None,
    )

    assert y.get_value() == [1, 2, 3]


@pytest.mark.parametrize("indices,artist_index,xdata,ydata,args,quib_index,expected_value,tolerance", [
    ([0], 0, 1, 2, (iquib([30, 50, 100]), iquib([10, 20, 30])), [0, 1], ([1, 50, 100], [2, 20, 30]), None),
], ids=[
    "xdata&ydata",
])
def test_scatter_inverse_assigner(mock_scatter, indices, artist_index, xdata, ydata, args, quib_index, expected_value, tolerance):
    pick_event, mouse_event = create_mock_pick_event_and_mouse_event(indices, xdata, ydata, artist_index)

    with GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.temporary_set(tolerance):
        inverse_assign_drawing_func(
            enhanced_pick_event=TempEnhancedPickEvent.from_pick_event_and_func_args_kwargs(
                pick_event=pick_event,
                func_args_kwargs=FuncArgsKwargs(mock_scatter, (None, *args), {})),
            mouse_event=mouse_event,
        )

    if isinstance(quib_index, int):
        quib_index = [quib_index]
        expected_value = [expected_value]
    for index, expected in zip(quib_index, expected_value):
        assert np.array_equal(args[index].get_value(), expected)


