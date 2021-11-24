import operator
from unittest import mock

import numpy as np
import pytest

from pyquibbler.quib.assignment import BoundAssignmentTemplate, RangeAssignmentTemplate
from pyquibbler.quib.refactor.factory import create_quib
from pyquibbler.quib.refactor.quib import Quib
from tests.functional.quib.utils import get_mock_with_repr, slicer


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


# TODO: should following override tests be in a separate place? (hint: they should)

def test_quib_override_without_assignment_template():
    mock_func = mock.Mock()
    mock_func.return_value = ['old item']
    quib = create_quib(func=mock_func, allow_overriding=True)
    new_item = 'new item'
    quib[0] = new_item

    assert quib.get_value()[0] is new_item


def test_quib_override_with_assignment_template():
    mock_assignment_template = mock.Mock(spec=BoundAssignmentTemplate)
    mock_assignment_template.convert.return_value = "something that wont change on deepcopy"
    quib = create_quib(func=mock.Mock(return_value=['oh no']), allow_overriding=True)
    quib.set_assignment_template(mock_assignment_template)
    quib[0] = 'val'

    result = quib[0].get_value()

    mock_assignment_template.convert.assert_called_with('val')
    assert result == mock_assignment_template.convert.return_value


def test_overrides_are_applied_in_order():
    quib = create_quib(mock.Mock(return_value=[2]), allow_overriding=True)
    quib[0] = 1
    quib[0] = -1

    assert quib[0].get_value() == -1


def test_quib_get_override_list_shows_user_friendly_information_about_overrides():
    quib = create_quib(func=mock.Mock(return_value=["1"]), allow_overriding=True)
    key_repr = 'key_repr'
    value_repr = 'value_repr'
    key_mock = get_mock_with_repr(key_repr)
    value_mock = get_mock_with_repr(value_repr)
    quib[key_mock] = value_mock

    overrides_repr = repr(quib.get_override_list())

    assert key_repr in overrides_repr
    assert value_repr in overrides_repr


### TODO: END OVERRIDING TESTS


def test_quib_get_shape():
    arr = np.array([1, 2, 3])
    quib = create_quib(mock.Mock(return_value=arr))

    assert quib.get_shape() == arr.shape


@pytest.mark.parametrize(['data', 'overrides', 'expected_mask'], [
    ([], [], []),
    ([0], [], [False]),
    ([0], [(0, 1)], [True]),
    ([0, 1], [], [False, False]),
    ([0, 1], [(1, 2)], [False, True]),
    ([[0, 1], [2, 3]], [(1, [4, 5])], [[False, False], [True, True]]),
    ([[0, 1], [2, 3]], [((0, 0), 5)], [[True, False], [False, False]]),
    ([[0, 1], [2, 3]], [(slicer[:], 5)], [[True, True], [True, True]]),
])
def test_quib_get_inversed_quibs_with_assignments(data, overrides, expected_mask):
    quib = create_quib(func=mock.Mock(return_value=np.array(data)), allow_overriding=True)
    for key, value in overrides:
        quib[key] = value
    assert np.array_equal(quib.get_override_mask().get_value(), expected_mask)

# TODO: when done with translation...
# @pytest.mark.regression
# def test_quib_get_override_mask_with_list():
#     quib = create_quib(func=mock.Mock(return_value=[10, [21, 22], 30]), allow_overriding=True)
#     quib[1][1] = 222
#
#     mask = quib.get_override_mask()
#
#     assert mask.get_value() == [False, [False, True], False]
#
#


# TODO: Where should iter tests be? Is this ok?
def test_quib_iter_first(quib):
    quib.func.return_value = [1, 2, 3]
    first, second = quib.iter_first()

    assert (first.get_value(), second.get_value()) == tuple(quib.func.return_value[:2])


def test_quib_getitem(quib):
    quib.func.return_value = [1, 2, 3]

    getitem_quib = quib[0]

    assert getitem_quib.func == operator.getitem
    assert getitem_quib.get_value() == quib.func.return_value[0]
