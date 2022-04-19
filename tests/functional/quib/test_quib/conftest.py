from unittest import mock

import matplotlib.pyplot as plt
import pytest
from matplotlib.artist import Artist

from pyquibbler import Quib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
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
    add_definition_for_function(func=func, func_definition=create_func_definition(is_graphics=True, lazy=True))
    return create_quib(
        func=func,
        args=(quib,),
        kwargs={},
    )


@pytest.fixture
def axes() -> plt.Axes:
    from matplotlib import pyplot as plt
    plt.close("all")
    plt.gcf().set_size_inches(8, 6)
    return plt.gca()


@pytest.fixture()
def create_artist(mock_axes):

    def _create(*args):
        # We need this in order for artist to be tracked
        artist = Artist()
        artist.axes = mock_axes
        artist.figure = mock.Mock()
        mock_axes.artists.append(artist)
        return artist

    return _create

