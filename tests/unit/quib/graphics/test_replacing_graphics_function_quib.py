from unittest import mock

from matplotlib.artist import Artist
from matplotlib.axes import Axes

from pyquibbler import iquib
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

    first_quib.invalidate_and_redraw(path=[...])

    assert mock_func.call_count == 2
