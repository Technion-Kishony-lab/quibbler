from unittest import mock

import pytest
from matplotlib.artist import Artist
from matplotlib.axes import Axes

from pyquibbler import iquib
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.graphics.replacing_graphics_function_quib import ReplacingGraphicsFunctionQuib


def test_replacing_graphics_function_quib():
    first_quib = iquib(5)
    mock_artist = mock.Mock(spec=Axes)
    mock_func = mock.Mock()
    mock_func.__name__ = "myfunc"
    # Creating runs the quibs- it's also important to keep them as a local var so they don't get garbage collected
    # if they are the test will pass regardless
    _ = ReplacingGraphicsFunctionQuib.create(
        func=mock_func,
        func_args=(mock_artist, first_quib)
    )
    __ = ReplacingGraphicsFunctionQuib.create(
        func=mock_func,
        func_args=(mock_artist,)
    )

    first_quib.invalidate_and_redraw_at_path(path=[...])

    assert mock_func.call_count == 2


@pytest.mark.regression
def test_replacing_graphics_function_quib_doesnt_remove_quib_after_invalidation_three_times():
    first_quib = iquib(5)
    mock_artist = mock.Mock(spec=Axes)
    mock_func = mock.Mock()
    mock_func.__name__ = "myfunc"
    path = [PathComponent(component=..., indexed_cls=first_quib.get_type())]

    # First time to create quib, attach to parent, attach to axes
    _ = ReplacingGraphicsFunctionQuib.create(
        func=mock_func,
        func_args=(mock_artist, first_quib),
    )
    # Second time to potentially remove from axes (this was the bug)
    first_quib.invalidate_and_redraw_at_path(path=path)
    # Third time to make sure we DID stay attached to our parent
    first_quib.invalidate_and_redraw_at_path(path=path)

    assert mock_func.call_count == 3
