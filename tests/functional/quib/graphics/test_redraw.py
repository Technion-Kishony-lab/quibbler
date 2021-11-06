from unittest.mock import Mock

from pyquibbler.quib.graphics import redraw_axeses
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode


def test_redraw_axes_happy_flow(mock_axes):
    redraw_axeses({mock_axes})

    mock_axes.figure.canvas.draw.assert_called_once()


def test_redraw_in_aggregate_mode(mock_axes):
    with aggregate_redraw_mode():
        redraw_axeses({mock_axes})
        redraw_axeses({mock_axes})
        redraw_axeses({mock_axes})

    mock_axes.figure.canvas.draw.assert_called_once()


def test_redraw_axeses_does_not_redraw_same_canvas_twice():
    mock_axes1 = Mock()
    mock_axes2 = Mock()
    mock_canvas = Mock()
    mock_axes1.figure.canvas = mock_canvas
    mock_axes2.figure.canvas = mock_canvas

    redraw_axeses({mock_axes1, mock_axes2})

    mock_canvas.draw.assert_called_once()
