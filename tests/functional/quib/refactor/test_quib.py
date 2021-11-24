from unittest import mock

import pytest

from pyquibbler.quib.refactor.factory import create_quib
from pyquibbler.quib.refactor.quib import Quib


@pytest.fixture()
def quib():
    return Quib(
        func=mock.Mock(),
        args=tuple(),
        kwargs={},
        allow_overriding=False,
        assignment_template=None,
        cache_behavior=None,
        is_known_graphics_func=False
    )


@pytest.fixture()
def graphics_quib(quib):
    return create_quib(
        func=mock.Mock(),
        args=(quib,),
        kwargs={},
        is_known_graphics_func=True
    )


def test_quib_invalidate_and_redraw_calls_children_with_graphics(quib, graphics_quib):
    quib.invalidate_and_redraw_at_path()

    graphics_quib.func.assert_called_once()


def test_quib_does_not_redraw_when_child_is_not_graphics_quib(quib):
    non_graphics_quib = create_quib(func=mock.Mock(), args=(quib,), kwargs={})

    quib.invalidate_and_redraw_at_path()

    non_graphics_quib.func.assert_not_called()


def test_quib_removes_dead_children_automatically(quib):
    mock_func = mock.Mock()
    child = create_quib(func=mock_func, args=(quib,), kwargs={}, is_known_graphics_func=True)
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

