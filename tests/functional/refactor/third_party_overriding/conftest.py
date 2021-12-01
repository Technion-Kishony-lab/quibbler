from unittest import mock

import pytest

from pyquibbler.quib.refactor.factory import create_quib


@pytest.fixture()
def quib():
    return create_quib(func=mock.Mock())


@pytest.fixture
def mock_module():
    return mock.Mock()


@pytest.fixture
def func_name_to_override():
    return "hello_my_good_good_friend"


@pytest.fixture
def func_mock_on_module(mock_module, func_name_to_override):
    return getattr(mock_module, func_name_to_override)


@pytest.fixture()
def overriden_func(mock_module, func_name_to_override):
    return lambda *a: getattr(mock_module, func_name_to_override)(*a)
