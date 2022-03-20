from unittest import mock
from unittest.mock import Mock

from pyquibbler import iquib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode, redraw_axeses


def test_redraw_axes_happy_flow(mock_axes):
    redraw_axeses({mock_axes})

    mock_axes.figure.canvas.draw.assert_called_once()


def test_redraw_in_aggregate_mode():
    mock_func = mock.Mock()
    quib = iquib(1)
    add_definition_for_function(func=mock_func, function_definition=create_func_definition(is_graphics_func=True,
                                                                                           replace_previous_quibs_on_artists=True))
    _ = create_quib(func=mock_func, args=(quib,))
    assert mock_func.call_count == 0, "sanity"

    with aggregate_redraw_mode():
        quib.handler.invalidate_and_redraw_at_path([])
        quib.handler.invalidate_and_redraw_at_path([])
        quib.handler.invalidate_and_redraw_at_path([])

    assert mock_func.call_count == 1


def test_redraw_axeses_does_not_redraw_same_canvas_twice():
    mock_axes1 = Mock()
    mock_axes2 = Mock()
    mock_canvas = Mock()
    mock_axes1.figure.canvas = mock_canvas
    mock_axes2.figure.canvas = mock_canvas

    redraw_axeses({mock_axes1, mock_axes2})

    mock_canvas.draw.assert_called_once()
