from unittest import mock

import pytest

from pyquibbler.quib.assignment import BoundAssignmentTemplate, RangeAssignmentTemplate
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


@pytest.mark.regression
def test_quib_invalidates_children_recursively(quib, create_mock_quib):
    child = create_quib(func=mock.Mock(), args=(quib,), kwargs={})
    grandchild = create_mock_quib()
    child.add_child(grandchild)

    quib.invalidate_and_redraw_at_path([])

    grandchild._invalidate_quib_with_children_at_path.assert_called_once()


@pytest.mark.parametrize(['args', 'expected_template'], [
    ((BoundAssignmentTemplate(2, 4),), BoundAssignmentTemplate(2, 4)),
    ((1, 2), BoundAssignmentTemplate(1, 2)),
    ((1, 2, 3), RangeAssignmentTemplate(1, 2, 3))
])
def test_set_and_get_assignment_template(args, expected_template, quib):
    quib.set_assignment_template(*args)
    template = quib.get_assignment_template()

    assert template == expected_template


@pytest.mark.parametrize('args', [(), (1, 2, 3, 4)])
def test_set_assignment_template_with_wrong_number_of_args_raises_typeerror(args, quib):
    with pytest.raises(TypeError):
        quib.set_assignment_template(*args)


def test_set_assignment_template_with_range(quib):
    quib.set_assignment_template(1, 2, 3)
    template = quib.get_assignment_template()

    assert template == RangeAssignmentTemplate(1, 2, 3)


# TODO: should override this be in a separate place? (hint: they should)
def test_quib_override_without_assignment_template(quib):
    mock_func = mock.Mock()
    mock_func.return_value = ['old item']
    quib = create_quib(func=mock_func, allow_overriding=True)
    new_item = 'new item'
    quib[0] = new_item

    assert quib.get_value()[0] is new_item

