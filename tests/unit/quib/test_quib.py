import operator
import magicmethods
import numpy as np
from unittest import mock
from unittest.mock import Mock
from pytest import mark, raises, fixture

from pyquibbler.quib import Quib
from pyquibbler.quib.assignment import RangeAssignmentTemplate, BoundAssignmentTemplate
from pyquibbler.quib.graphics import GraphicsFunctionQuib
from pyquibbler.quib.quib import QuibIsNotNdArrayException

from .utils import get_mock_with_repr, slicer


class ExampleQuib(Quib):
    def __init__(self, value, assignment_template=None):
        super().__init__(assignment_template=assignment_template)
        self.value = value
        self.invalidate_count = 0

    def _invalidate(self):
        self.invalidate_count += 1

    def _get_inner_value(self):
        return self.value


@fixture
def example_quib(assignment_template_mock):
    return ExampleQuib(['the', 'quib', 'value'], assignment_template=assignment_template_mock)


@fixture
def assignment_template_mock():
    mock = Mock()
    mock.convert.return_value = 'assignment_template_mock.convert.return_value'
    return mock


def test_quib_getitem(example_quib):
    got = example_quib[0]

    assert got.get_value() is example_quib.value[0]


def test_quib_invalidate_and_redraw_calls_graphics_function_quib_children(example_quib):
    mock_func = mock.Mock()
    mock_func.return_value = []
    quib = GraphicsFunctionQuib(func=mock_func, args=tuple(), kwargs={}, artists=[], cache_behavior=None)
    example_quib.add_child(quib)

    example_quib.invalidate_and_redraw()

    mock_func.assert_called_once()


@mark.parametrize('operator_name', set(magicmethods.arithmetic) - {'__div__', '__divmod__'})
def test_quib_forward_and_reverse_binary_operators(operator_name: str):
    op = getattr(operator, operator_name, None)
    quib1 = ExampleQuib(1)
    quib2 = ExampleQuib(2)

    # Forward operators
    assert op(quib1, quib2).get_value() == op(quib1.value, quib2.value)
    assert op(quib1, quib2.value).get_value() == op(quib1.value, quib2.value)
    # Reverse operators
    assert op(quib1.value, quib2).get_value() == op(quib1.value, quib2.value)


def test_quib_removes_dead_children_automatically():
    quib = ExampleQuib('something')
    child = ExampleQuib('child')
    child_invalidate = child._invalidate = Mock()
    quib.add_child(child)
    del child
    quib.invalidate_and_redraw()

    child_invalidate.assert_not_called()


@mark.regression
def test_quib_invalidates_children_recursively(example_quib):
    child = ExampleQuib(mock.Mock())
    example_quib.add_child(child)
    grandchild = ExampleQuib(mock.Mock())
    child.add_child(grandchild)

    example_quib.invalidate_and_redraw()

    assert child.invalidate_count == 1
    assert grandchild.invalidate_count == 1


@mark.parametrize(['args', 'expected_template'], [
    ((BoundAssignmentTemplate(2, 4),), BoundAssignmentTemplate(2, 4)),
    ((1, 2), BoundAssignmentTemplate(1, 2)),
    ((1, 2, 3), RangeAssignmentTemplate(1, 2, 3))
])
def test_set_assignment_template(args, expected_template, example_quib):
    example_quib.set_assignment_template(*args)
    template = example_quib.get_assignment_template()

    assert template == expected_template


@mark.parametrize('args', [(), (1, 2, 3, 4)])
def test_set_assignment_template_with_wrong_number_of_args_raises_typeerror(args, example_quib):
    with raises(TypeError):
        example_quib.set_assignment_template(*args)


def test_set_assignment_template_with_range(example_quib):
    example_quib.set_assignment_template(1, 2, 3)
    template = example_quib.get_assignment_template()

    assert template == RangeAssignmentTemplate(1, 2, 3)


def test_quib_override_without_assignment_template():
    quib = ExampleQuib(['old item'])
    new_item = 'new item'
    quib[0] = new_item

    assert quib.get_value()[0] is new_item


def test_quib_override_with_assignment_template(example_quib, assignment_template_mock):
    example_quib[0] = 'val'
    result = example_quib[0].get_value()

    assignment_template_mock.convert.assert_called_with('val')
    assert result == assignment_template_mock.convert.return_value


def test_quib_updates_override_after_assignment_template_changed(example_quib, assignment_template_mock):
    example_quib[0] = 'val'
    item = example_quib[0]
    new_assignment_template = Mock()
    new_assignment_template.convert.return_value = 'new_assignment_template.convert.return_value'
    example_quib.set_assignment_template(new_assignment_template)

    result = item.get_value()

    assignment_template_mock.convert.assert_not_called()
    new_assignment_template.convert.assert_called_with('val')
    assert result == new_assignment_template.convert.return_value


def test_overrides_are_applied_in_order():
    quib = ExampleQuib([0])
    quib[0] = 1
    quib[0] = -1

    assert quib[0].get_value() == -1


def test_quib_get_override_list_shows_user_friendly_information_about_overrides(example_quib):
    key_repr = 'key_repr'
    value_repr = 'value_repr'
    key_mock = get_mock_with_repr(key_repr)
    value_mock = get_mock_with_repr(value_repr)
    example_quib[key_mock] = value_mock

    overrides_repr = repr(example_quib.get_override_list())

    assert key_repr in overrides_repr
    assert value_repr in overrides_repr


def test_quib_get_shape():
    arr = np.array([1, 2, 3])
    quib = ExampleQuib(arr)

    assert quib.get_shape().get_value() == arr.shape


def test_quib_get_shape_with_non_ndarray_quib(example_quib):
    with raises(QuibIsNotNdArrayException):
        example_quib.get_shape().get_value()


@mark.parametrize(['data', 'overrides', 'expected_mask'], [
    ([], [], []),
    ([0], [], [False]),
    ([0], [(0, 1)], [True]),
    ([0, 1], [], [False, False]),
    ([0, 1], [(1, 2)], [False, True]),
    ([[0, 1], [2, 3]], [(1, [4, 5])], [[False, False], [True, True]]),
    ([[0, 1], [2, 3]], [((0, 0), 5)], [[True, False], [False, False]]),
    ([[0, 1], [2, 3]], [(slicer[:], 5)], [[True, True], [True, True]]),
])
def test_quib_get_override_mask(data, overrides, expected_mask):
    quib = ExampleQuib(np.array(data))
    for key, value in overrides:
        quib[key] = value
    assert np.array_equal(quib.get_override_mask().get_value(), expected_mask)


def test_quib_unpack_one():
    one, = ExampleQuib.create((1,))

    assert one.get_value() == 1


def test_quib_unpack_two():
    one, two = ExampleQuib.create((1, 2))

    assert (one.get_value(), two.get_value()) == (1, 2)


def test_quib_unpack_too_little():
    one, two = ExampleQuib.create((1,))
    # Should that actually work?
    assert one.get_value() == 1
    with raises(IndexError):
        two.get_value()

# Should fail:
# one, = ExampleQuib.create((1, 2))
# Should work:
# one, *others, bla = ExampleQuib.create((1, 2))
