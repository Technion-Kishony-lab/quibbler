from unittest import mock

import pytest

from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.third_party_overriding.graphics_overriding import GraphicsOverrideDefinition


@pytest.fixture
def mock_module():
    return mock.Mock()


@pytest.fixture
def func_name_to_override():
    return "hello_my_good_good_friend"


@pytest.fixture
def func_mock_on_module(mock_module, func_name_to_override):
    return getattr(mock_module, func_name_to_override)


@pytest.fixture(autouse=True)
def graphics_definition(mock_module, func_name_to_override, func_mock_on_module):
    definition = GraphicsOverrideDefinition(func_name=func_name_to_override, module_or_cls=mock_module)
    definition.override()
    return definition


@pytest.fixture()
def overriden_func(mock_module, func_name_to_override):
    return getattr(mock_module, func_name_to_override)


def test_graphics_func_does_run_by_default(overriden_func, func_mock_on_module):
    overriden_func()

    assert func_mock_on_module.call_count == 1


def test_graphics_func_does_not_run_when_evaluate_now_flag_set_to_false(overriden_func, func_mock_on_module):
    with GRAPHICS_EVALUATE_NOW.temporary_set(False):
        overriden_func()

    assert func_mock_on_module.call_count == 0
