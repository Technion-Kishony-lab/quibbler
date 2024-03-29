from unittest import mock

import pytest

from pyquibbler import Quib
from pyquibbler.quib.factory import create_quib


@pytest.fixture()
def quib() -> Quib:
    return create_quib(func=mock.Mock())


@pytest.fixture
def mock_module():
    mdl = mock.Mock()
    mdl.__name__ = 'MockModule'
    return mdl

@pytest.fixture
def func_name_to_override():
    return "hello_my_good_good_friend"


@pytest.fixture
def func_mock_on_module(mock_module, func_name_to_override):
    return getattr(mock_module, func_name_to_override)


@pytest.fixture()
def overridden_func(mock_module, func_name_to_override):
    return lambda *a: getattr(mock_module, func_name_to_override)(*a)
