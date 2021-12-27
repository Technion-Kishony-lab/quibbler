from unittest import mock

import pytest

from pyquibbler.refactor.quib.factory import create_quib
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.overriding import override_third_party_funcs


@pytest.fixture(autouse=True)
def override_all():
    override_third_party_funcs()


@pytest.fixture
def create_quib_with_return_value():
    def _create(ret_val, allow_overriding=False):
        return create_quib(mock.Mock(return_value=ret_val), allow_overriding=allow_overriding)
    return _create


@pytest.fixture()
def quib():
    return Quib(
        func=mock.Mock(return_value=[1, 2, 3]),
        args=tuple(),
        kwargs={},
        allow_overriding=False,
        assignment_template=None,
        cache_behavior=None,
        is_known_graphics_func=False,
        name=None,
        line_no=None,
        file_name=None,
        is_random_func=False,
        call_func_with_quibs=False
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
    return create_quib(
        func=mock.Mock(),
        args=(quib,),
        kwargs={},
        is_known_graphics_func=True
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
