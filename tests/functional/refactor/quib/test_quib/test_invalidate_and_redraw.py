from unittest import mock

import pytest

from pyquibbler import CacheBehavior
from pyquibbler.cache.cache import CacheStatus
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib


def test_quib_invalidate_and_redraw_calls_children_with_graphics(quib, graphics_quib):
    quib.invalidate_and_redraw_at_path()

    graphics_quib.func.assert_called_once()


def test_quib_does_not_redraw_when_child_is_not_graphics_quib(quib):
    non_graphics_quib = create_quib(func=mock.Mock(), args=(quib,), kwargs={})

    quib.invalidate_and_redraw_at_path()

    non_graphics_quib.func.assert_not_called()


def test_quib_removes_dead_children_automatically(quib):
    mock_func = mock.Mock()
    add_definition_for_function(func=mock_func,
                                function_definition=create_func_definition(is_known_graphics_func=True))
    child = create_quib(func=mock_func, args=(quib,), kwargs={})
    quib.add_child(child)

    del child
    quib.invalidate_and_redraw_at_path(path=[])

    mock_func.assert_not_called()


@pytest.mark.regression
def test_quib_invalidates_children_recursively(quib, create_mock_quib):
    child = create_quib(func=mock.Mock(), args=(quib,), kwargs={})
    grandchild = create_mock_quib()
    child.add_child(grandchild)

    quib.invalidate_and_redraw_at_path([])

    grandchild._invalidate_quib_with_children_at_path.assert_called_once()


def create_child_with_valid_cache(parent):
    child = create_quib(func=mock.Mock(), args=(parent,), kwargs={}, cache_behavior=CacheBehavior.ON)
    child.get_value()
    # Sanity
    assert child.cache_status == CacheStatus.ALL_VALID
    return child


@pytest.mark.regression
def test_quib_invalidates_children_recursively(quib, create_mock_quib):
    child = create_child_with_valid_cache(quib)
    grandchild = create_child_with_valid_cache(child)

    quib.invalidate_and_redraw_at_path([])

    assert child.cache_status == CacheStatus.ALL_INVALID
    assert grandchild.cache_status == CacheStatus.ALL_INVALID


def test_quib_invalidates_all_when_invalidated_at_param_source(quib, create_quib_with_return_value):
    param_source = create_quib_with_return_value(3, allow_overriding=True)
    quib_with_param_source = create_quib(func=mock.Mock(), args=(param_source,))

    # By default everything is considered a param source
    param_source.assign_value(5)

    assert quib_with_param_source.cache_status == CacheStatus.ALL_INVALID

