from unittest import mock

import pytest

from pyquibbler import CacheBehavior
from pyquibbler.refactor.cache.cache import CacheStatus
from pyquibbler.refactor.function_definitions import add_definition_for_function
from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.quib.factory import create_quib


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
                                function_definition=create_function_definition(is_known_graphics_func=True))
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


# TODO: Should work when caching is implemented
@pytest.mark.regression
def test_quib_invalidates_children_recursively(quib, create_mock_quib):
    child = create_child_with_valid_cache(quib)
    grandchild = create_child_with_valid_cache(child)

    quib.invalidate_and_redraw_at_path([])

    assert child.cache_status == CacheStatus.ALL_INVALID
    assert grandchild.cache_status == CacheStatus.ALL_INVALID
