from unittest import mock

import pytest
from matplotlib.artist import Artist

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.function_definition import create_function_definition
from pyquibbler.graphics.global_collecting import overridden_graphics_function
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.quib import Quib


@pytest.fixture
def create_quib_with_return_value():
    def _create(ret_val, allow_overriding=False, evaluate_now=False):
        return create_quib(mock.Mock(return_value=ret_val), allow_overriding=allow_overriding,
                           evaluate_now=evaluate_now)
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
def create_mock_quib():
    def _create(shape=None, get_value_result=None, children=None):
        shape = shape or (3, 1)
        get_value_result = get_value_result or [[1, 2, 3]]
        mock_quib = mock.Mock(spec=Quib)
        mock_quib.get_value_valid_at_path.return_value = get_value_result
        mock_quib.get_shape.return_value = shape
        mock_quib.get_ndim.return_value = len(shape)
        mock_quib.get_axeses.return_value = []
        mock_quib._get_children_recursively.return_value = children or set()
        return mock_quib
    return _create


@pytest.fixture()
def graphics_quib(quib):
    func = mock.Mock()
    add_definition_for_function(func=func, function_definition=create_function_definition(is_known_graphics_func=True))
    return create_quib(
        func=func,
        args=(quib,),
        kwargs={},
    )


@pytest.fixture
def axes():
    from matplotlib import pyplot as plt
    plt.close("all")
    plt.gcf().set_size_inches(8, 6)
    return plt.gca()


@pytest.fixture()
def mock_axes():
    axes = mock.Mock()
    axes.figure.canvas.supports_blit = False
    axes.artists = []
    return axes


@pytest.fixture()
def create_artist(mock_axes):

    def _create(*args):
        # We need this in order for artist to be tracked
        with overridden_graphics_function():
            artist = Artist()
            artist.axes = mock_axes
            artist.figure = mock.Mock()
            mock_axes.artists.append(artist)
        return artist

    return _create

