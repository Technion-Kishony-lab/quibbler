import matplotlib.pyplot as plt

from unittest import mock
from unittest.mock import Mock

import numpy as np
import pytest

from pyquibbler import iquib, Project
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode, redraw_axeses
from weakref import ref


@pytest.fixture
def figure() -> plt.Figure:
    plt.close("all")
    figure = plt.figure()
    figure.canvas = Mock()
    return figure


@pytest.fixture
def axes1(figure) -> plt.Axes:
    axes1 = figure.add_axes([0, 0, 0.5, 1])
    return axes1


@pytest.fixture
def axes2(figure) -> plt.Axes:
    axes2 = figure.add_axes([0.5, 0, 0.5, 1])
    return axes2


def test_redraw_axes_happy_flow(figure, axes1):
    redraw_axeses({axes1})

    figure.canvas.draw.assert_called_once()


def test_redraw_in_aggregate_mode():
    mock_func = mock.Mock()
    quib = iquib(1)
    add_definition_for_function(func=mock_func, func_definition=create_func_definition(is_graphics=True,
                                                                                       lazy=True,
                                                                                       is_artist_setter=True))
    _ = create_quib(func=mock_func, args=(quib,))
    assert mock_func.call_count == 0, "sanity"

    with aggregate_redraw_mode():
        quib.handler.invalidate_and_redraw_at_path([])
        quib.handler.invalidate_and_redraw_at_path([])
        quib.handler.invalidate_and_redraw_at_path([])

    assert mock_func.call_count == 1


def test_only_notify_override_changes_once_in_aggregate_mode():
    mock_func = mock.Mock()
    quib = iquib([1, 2])
    Project.notify_of_overriding_changes = mock_func
    with aggregate_redraw_mode():
        quib[0] = 10
        quib[1] = 20

    assert mock_func.call_count == 1


def test_redraw_axeses_does_not_redraw_same_canvas_twice(figure, axes1, axes2):
    redraw_axeses({axes1, axes2})

    figure.canvas.draw.assert_called_once()


# To prevent pyimageXX bug in TK on notebook. see issue: #119
@pytest.mark.regression
def test_redraw_after_figure_closed(figure, axes1):
    plt.close(figure)
    redraw_axeses({axes1})
    figure.canvas.draw.assert_not_called()


# this test only works on jupyter notebook:
#
# def test_quibs_deleted_after_figure_closed():
#     figure = plt.figure()
#     axes1 = figure.gca()
#     a = iquib(np.array([1, 2]))
#     b = axes1.plot(a, picker=True)
#     ref_a = ref(a)
#     ref_b = ref(b)
#     del a, b
#     plt.close(figure)
#
#     assert ref_a() is None
#     assert ref_b() is None


def test_quibs_deleted_after_figure_clf(figure, axes1):
    a = iquib(np.array([1, 2]))
    b = axes1.plot(a, picker=True)
    ref_a = ref(a)
    ref_b = ref(b)
    del a, b
    figure.clf()

    assert ref_a() is None
    assert ref_b() is None


def test_quibs_deleted_after_axes_cla(figure, axes1):
    a = iquib(np.array([1, 2]))
    b = axes1.plot(a, picker=True)
    ref_a = ref(a)
    ref_b = ref(b)
    del a, b
    axes1.cla()

    assert ref_a() is None
    assert ref_b() is None
