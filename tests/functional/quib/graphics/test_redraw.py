from unittest import mock

import pytest

from pyquibbler.quib.graphics import redraw_axes
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode


@pytest.fixture()
def mock_axes():
    axes = mock.Mock()
    axes.figure.canvas.supports_blit = False
    return axes


def test_redraw_axes_happy_flow(mock_axes):

    redraw_axes(mock_axes)

    mock_axes.figure.canvas.draw.assert_called_once()


def test_redraw_in_aggregate_mode(mock_axes):

    with aggregate_redraw_mode():
        redraw_axes(mock_axes)
        redraw_axes(mock_axes)
        redraw_axes(mock_axes)

    mock_axes.figure.canvas.draw.assert_called_once()
