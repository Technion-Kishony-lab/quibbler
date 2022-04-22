import matplotlib.pyplot as plt

from unittest import mock
from unittest.mock import Mock

import pytest

from pyquibbler import iquib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode, redraw_axeses



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
                                                                                       replace_previous_quibs_on_artists=True))
    _ = create_quib(func=mock_func, args=(quib,))
    assert mock_func.call_count == 0, "sanity"

    with aggregate_redraw_mode():
        quib.handler.invalidate_and_redraw_at_path([])
        quib.handler.invalidate_and_redraw_at_path([])
        quib.handler.invalidate_and_redraw_at_path([])

    assert mock_func.call_count == 1


def test_redraw_axeses_does_not_redraw_same_canvas_twice(figure, axes1, axes2):
    redraw_axeses({axes1, axes2})

    figure.canvas.draw.assert_called_once()


def test_redraw_after_figure_closed(figure, axes1):
    plt.close(figure)
    redraw_axeses({axes1})
    figure.canvas.draw.assert_not_called()

