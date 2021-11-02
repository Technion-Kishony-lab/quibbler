import pytest
from unittest import mock

from pyquibbler.quib.graphics import redraw_axes
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode


def test_redraw_axes_happy_flow(mock_axes):
    redraw_axes(mock_axes)

    mock_axes.figure.canvas.draw.assert_called_once()


def test_redraw_in_aggregate_mode(mock_axes):
    with aggregate_redraw_mode():
        redraw_axes(mock_axes)
        redraw_axes(mock_axes)
        redraw_axes(mock_axes)

    mock_axes.figure.canvas.draw.assert_called_once()
