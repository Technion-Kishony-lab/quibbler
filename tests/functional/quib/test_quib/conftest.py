from unittest import mock

import matplotlib.pyplot as plt
import pytest
from matplotlib.artist import Artist

from pyquibbler import Quib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
from pyquibbler.quib.factory import create_quib


@pytest.fixture
def create_quib_with_return_value():
    def _create(ret_val, allow_overriding=False, lazy=True):
        return create_quib(mock.Mock(return_value=ret_val), allow_overriding=allow_overriding,
                           lazy=lazy)
    return _create


@pytest.fixture()
def quib():
    return create_quib(
        func=mock.Mock(return_value=[1, 2, 3]),
        args=tuple(),
        kwargs={},
        allow_overriding=False,
    )


@pytest.fixture()
def graphics_quib(quib) -> Quib:
    func = mock.Mock()
    add_definition_for_function(func=func, func_definition=create_or_reuse_func_definition(is_graphics=True))
    return create_quib(
        func=func,
        args=(quib,),
        kwargs={},
    )


@pytest.fixture
def figure() -> plt.Figure:
    from matplotlib import pyplot as plt
    plt.close("all")
    fig = plt.gcf()
    fig.set_size_inches(8, 6)
    return fig


@pytest.fixture
def axes(figure) -> plt.Axes:
    return figure.gca()


@pytest.fixture()
def create_artist(mock_axes):

    def _create(*args):
        # We need this in order for artist to be tracked
        artist = Artist()
        artist.axes = mock_axes
        artist.figure = mock.Mock()
        mock_axes._children.append(artist)
        return artist

    return _create

