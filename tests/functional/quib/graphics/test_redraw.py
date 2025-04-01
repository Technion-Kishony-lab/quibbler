import gc

import matplotlib.pyplot as plt

from unittest import mock
from unittest.mock import Mock

import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode, redraw_figures
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


def test_redraw_axes_happy_flow(figure):
    redraw_figures({figure})

    figure.canvas.draw.assert_called_once()


def test_redraw_in_aggregate_mode():
    mock_func = mock.Mock()
    quib = iquib(1)
    add_definition_for_function(func=mock_func, func_definition=create_or_reuse_func_definition(is_graphics=True,
                                                                                                is_artist_setter=True))
    _ = create_quib(func=mock_func, args=(quib,))
    assert mock_func.call_count == 1, "sanity"

    with aggregate_redraw_mode():
        quib.handler.invalidate_and_aggregate_redraw_at_path([])
        quib.handler.invalidate_and_aggregate_redraw_at_path([])
        quib.handler.invalidate_and_aggregate_redraw_at_path([])

    assert mock_func.call_count == 2


def tests_artists_are_garbage_collected_upon_redraw(axes, live_artists):
    xy = iquib([0.6, 0.4])
    print(len(live_artists))
    axes.axis([0, 1, 0, 1])
    axes.plot(xy[0], xy[1], 'x')
    axes.text(xy[0], xy[1], 'label')
    assert len(live_artists) == 2
    xy[1] = 0.3
    assert len(live_artists) == 2
    axes.remove()


# To prevent pyimageXX bug in TK on notebook. see issue: #119
@pytest.mark.regression
def test_redraw_after_figure_closed(figure):
    plt.close(figure)
    redraw_figures({figure})
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

def test_figure_is_deleted():
    figure = plt.figure()
    plt.plot([1, 2, 3])
    ref_figure = ref(figure)
    plt.close(figure)
    del figure
    gc.collect()  # Explicitly invoke garbage collection
    assert ref_figure() is None  # Check if weak reference is None


def test_quibs_deleted_after_figure_clf():
    figure = plt.figure()
    a = iquib(np.array([1, 2]))
    b = plt.plot(a, picker=True)

    ref_figure = ref(figure)
    ref_a = ref(a)
    ref_b = ref(b)

    plt.close(figure)
    del figure, a, b
    gc.collect()

    assert ref_figure() is None
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


@pytest.mark.regression
def test_quiby_legend(figure, axes1):
    # used to fail because some of tge legend artists have axes=None. (they all have valid figure though)
    a = iquib(['first', 'second'])
    axes1.plot([1, 2, 3])
    axes1.plot([2, 3, 4])
    legend_quib = axes1.legend(a)
    a[1] = 'replaced'
    assert legend_quib.get_value().get_texts()[1].get_text() == 'replaced'


def test_plot_with_implicit_quiby_color_updates_when_color_changes(figure, axes1):
    color = iquib('r')
    p = axes1.plot([1, 2, 3], color)
    assert p.get_value()[0].get_color() == (1.0, 0.0, 0.0, 1)
    color.assign('b')
    assert p.get_value()[0].get_color() == (0.0, 0.0, 1.0, 1)


def test_plot_with_no_color_spec_maintains_color_when_updates(figure, axes1):
    data = iquib([1, 2, 3])
    axes1.plot([3, 2, 1])  # advance the color cycle before the quib plot
    p = axes1.plot(data)
    line1 = p.get_value()[0]
    axes1.plot([3,3, 3])  # to advance the color cycle after the quib plot

    data[1] = 1
    line2 = p.get_value()[0]

    assert np.array_equal(line1._y, [1, 2, 3]), "sanity"
    assert np.array_equal(line2._y, [1, 1, 3]), "sanity"

    assert line2.get_color() == line1.get_color()
