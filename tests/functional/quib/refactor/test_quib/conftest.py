from unittest import mock

import pytest

from pyquibbler.quib.refactor.factory import create_quib
from pyquibbler.quib.refactor.quib import Quib


@pytest.fixture
def create_quib_with_return_value():
    def _create(ret_val):
        return create_quib(mock.Mock(return_value=ret_val))
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
        file_name=None
    )


@pytest.fixture()
def graphics_quib(quib):
    return create_quib(
        func=mock.Mock(),
        args=(quib,),
        kwargs={},
        is_known_graphics_func=True
    )