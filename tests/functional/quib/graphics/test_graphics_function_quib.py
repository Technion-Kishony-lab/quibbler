import numpy as np
import pytest
from unittest import mock

from pyquibbler import iquib
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.graphics import GraphicsFunctionQuib


def get_graphics_quib(func):
    return GraphicsFunctionQuib(
        args=tuple(),
        kwargs={},
        cache_behavior=None,
        func=func,
        artists=[]
    )


def test_graphics_function_quib_get_value_returns_value():
    mock_func = mock.Mock(return_value='mock_func.return_value')
    quib = get_graphics_quib(mock_func)

    res = quib.get_value()

    assert res == mock_func.return_value


def test_graphics_function_quib_rerun_removes_artists_created(monkeypatch, mock_axes, mock_artists_collector):
    father_quib = iquib(1)
    quib = get_graphics_quib(mock.Mock())
    father_quib.add_child(quib)

    quib.get_value()
    father_quib.invalidate_and_redraw_at_path(path=[PathComponent(component=..., indexed_cls=np.ndarray)])

    assert len(mock_artists_collector.all_mock_artists_created) == 2
    assert len(mock_axes.artists) == 1


@pytest.mark.regression
def test_graphics_function_quib_doesnt_fail_on_removal_of_artists(axes):
    input_quib = iquib([1, 2, 3])
    axes.plot(input_quib)
    axes.cla()

    input_quib[0] = 10


def test_graphics_function_quib_copy_color(axes):
    input_quib = iquib([1., 2., 3.])
    plot_quib = axes.plot(input_quib)

    artist_color_upon_creation = plot_quib.get_value()[0].get_color()
    input_quib.invalidate_and_redraw_at_path()
    artist_color_after_redraw = plot_quib.get_value()[0].get_color()

    assert artist_color_upon_creation == artist_color_after_redraw


def test_graphics_function_quib_does_not_copy_color(axes):
    input_quib = iquib([1., 2., 3.])
    color_quib = iquib([1, 0, 0])
    plot_quib = axes.plot(input_quib, color=color_quib)

    artist_color_upon_creation = plot_quib.get_value()[0].get_color()
    color_quib[1] = 1
    artist_color_after_color_change = plot_quib.get_value()[0].get_color()

    assert artist_color_upon_creation == [1, 0, 0]
    assert artist_color_after_color_change == [1, 1, 0]
