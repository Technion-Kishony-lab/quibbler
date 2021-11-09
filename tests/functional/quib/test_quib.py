import operator
from math import trunc, floor, ceil
from typing import Set, Optional, List
from unittest import mock
from unittest.mock import Mock
import numpy as np
import pytest
from pyquibbler import iquib, quibbler_user_function
from pytest import mark, raises, fixture

from pyquibbler.input_validation_utils import InvalidArgumentException
from pyquibbler.quib import Quib, OverridingNotAllowedException
from pyquibbler.quib.assignment import RangeAssignmentTemplate, BoundAssignmentTemplate, Assignment
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.assignment.assignment_template import InvalidTypeException
from pyquibbler.quib.assignment.utils import FailedToDeepAssignException
from pyquibbler.quib.graphics import GraphicsFunctionQuib
from pyquibbler.quib.operator_overriding import ARITHMETIC_OVERRIDES, UNARY_OVERRIDES
from .utils import get_mock_with_repr, slicer


class ExampleQuib(Quib):
    _DEFAULT_ALLOW_OVERRIDING = True

    def __init__(self, value, assignment_template=None):
        super().__init__(assignment_template=assignment_template)
        self.value = value
        self.invalidate_count = 0
        self._parents = set()

    def add_parent(self, parent):
        self._parents.add(parent)

    def _invalidate_quib_with_children_at_path(self, invalidator_quib, path_component):
        self.invalidate_count += 1
        super()._invalidate_quib_with_children_at_path(invalidator_quib, path_component)

    def _get_inner_value_valid_at_path(self, path):
        return self.value

    def _get_inner_functional_representation_expression(self):
        return self.value

    @property
    def parents(self) -> Set[Quib]:
        return self._parents

    def _get_paths_for_children_invalidation(self, quib, path):
        return [path]


@fixture
def example_quib(assignment_template_mock):
    return ExampleQuib(['the', 'quib', 'value'], assignment_template=assignment_template_mock)


@fixture
def assignment_template_mock():
    mock = Mock()
    mock.convert.return_value = 'assignment_template_mock.convert.return_value'
    return mock


def test_quib_invalidate_and_redraw_calls_graphics_function_quib_children(example_quib):
    mock_func = mock.Mock()
    mock_func.return_value = []

    quib = GraphicsFunctionQuib(func=mock_func, args=tuple(), kwargs={}, cache_behavior=None)
    example_quib.add_child(quib)
    quib.get_value()  # we want to set cache to valid

    example_quib.invalidate_and_redraw_at_path(path=[])

    assert mock_func.call_count == 2  # once for our original get_value, once for the redraw after invalidation


@mark.parametrize(['val1', 'val2'], [
    (1, 2),
    (1., 2.),
    (1., 2),
    (1, 2.)
])
@mark.parametrize('operator_name', {override[1] for override in ARITHMETIC_OVERRIDES} - {'__matmul__', '__divmod__'})
def test_quib_forward_and_inverse_arithmetic_operators(operator_name: str, val1, val2):
    op = getattr(operator, operator_name)
    quib1 = ExampleQuib(val1)
    quib2 = ExampleQuib(val2)

    if (isinstance(val1, float) or isinstance(val2, float)) and operator_name in {'__rshift__', '__lshift__', '__or__',
                                                                                  '__and__', '__xor__'}:
        # Bitwise operators don't work with floats
        result_quib = op(quib1, quib2)
        with raises(TypeError):
            result_quib.get_value()

    else:
        # Forward operators
        assert op(quib1, quib2).get_value() == op(val1, val2)
        assert op(quib1, val2).get_value() == op(val1, val2)
        # Reverse operators
        assert op(val1, quib2).get_value() == op(val1, val2)


def test_quib_divmod():
    quib1 = ExampleQuib(1)
    quib2 = ExampleQuib(2)

    # Forward
    assert divmod(quib1, quib2).get_value() == divmod(quib1.value, quib2.value)
    assert divmod(quib1, quib2.value).get_value() == divmod(quib1.value, quib2.value)
    # Reverse
    assert divmod(quib1.value, quib2).get_value() == divmod(quib1.value, quib2.value)


@mark.parametrize('val', [1, 1., -1, -1.])
@mark.parametrize('operator_name', [override[1] for override in UNARY_OVERRIDES])
def test_quib_unary_operators(operator_name, val):
    op = getattr(operator, operator_name)
    quib = ExampleQuib(val)
    result_quib = op(quib)

    if isinstance(val, float) and operator_name in {'__invert__'}:
        # Bitwise operators don't work with floats
        with raises(TypeError):
            result_quib.get_value()
    else:
        assert result_quib.get_value() == op(val)


@mark.parametrize('val', [1, 1., -1, -1.])
@mark.parametrize('op', [round, trunc, floor, ceil])
def test_quib_rounding_operators(op, val):
    quib = ExampleQuib(val)
    result_quib = op(quib)

    result = result_quib.get_value()

    assert result == op(val)


def test_quib_removes_dead_children_automatically():
    quib = ExampleQuib('something')
    child = ExampleQuib('child')
    child_invalidate = child._invalidate = Mock()
    quib.add_child(child)
    del child
    quib.invalidate_and_redraw_at_path(path=[...])

    child_invalidate.assert_not_called()


@mark.regression
def test_quib_invalidates_children_recursively(example_quib):
    child = ExampleQuib(mock.Mock())
    example_quib.add_child(child)
    grandchild = ExampleQuib(mock.Mock())
    child.add_child(grandchild)

    example_quib.invalidate_and_redraw_at_path([PathComponent(component=..., indexed_cls=np.ndarray)])

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

    assert quib.get_shape() == arr.shape


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
def test_quib_get_inversed_quibs_with_assignments(data, overrides, expected_mask):
    quib = ExampleQuib(np.array(data))
    for key, value in overrides:
        quib[key] = value
    assert np.array_equal(quib.get_override_mask().get_value(), expected_mask)


@mark.regression
def test_quib_get_override_mask_with_list():
    quib = ExampleQuib([10, [21, 22], 30])
    quib[1][1] = 222

    mask = quib.get_override_mask()

    assert mask.get_value() == [False, [False, True], False]


@mark.regression
def test_quib_get_override_mask_with_override_removal():
    quib = ExampleQuib([0, [1, 2], 3])
    quib[:] = [9, [9, 9], 9]
    quib.remove_override([PathComponent(indexed_cls=quib.get_type(), component=1),
                          PathComponent(indexed_cls=list, component=0)])

    mask = quib.get_override_mask().get_value()

    assert mask == [True, [False, True], True]


def test_quib_iter_first(example_quib):
    first, second = example_quib.iter_first()

    assert (first.get_value(), second.get_value()) == tuple(example_quib.value[:2])


def test_quib_getitem(example_quib):
    function_quib = example_quib[0]

    assert function_quib.func == operator.getitem
    assert function_quib.get_value() == example_quib.value[0]


@mark.regression
def test_quib_add_with_float_does_not_return_not_implemented():
    function_quib = ExampleQuib(1)
    add_function_quib = function_quib + 1.2

    value = add_function_quib.get_value()

    assert value == 2.2


def test_quib_get_type(example_quib):
    assert example_quib.get_type() == list


def test_quib_assign_value(example_quib):
    example_quib.assign = mock.Mock()
    mock_value = mock.Mock()

    example_quib.assign_value(mock_value)

    example_quib.assign.assert_called_once_with(Assignment(path=[],
                                                           value=mock_value))


def test_quib_assign_value_to_key(example_quib):
    example_quib.assign = mock.Mock()
    mock_value = mock.Mock()
    mock_key = mock.Mock()

    example_quib.assign_value_to_key(value=mock_value, key=mock_key)

    example_quib.assign.assert_called_once_with(Assignment(path=[PathComponent(component=mock_key,
                                                                               indexed_cls=example_quib.get_type())],
                                                           value=mock_value))


def test_quib_override_when_overriding_not_allowed(example_quib):
    example_quib.set_allow_overriding(False)
    override = Mock()

    with raises(OverridingNotAllowedException) as exc_info:
        example_quib.override(override, allow_overriding_from_now_on=False)

    assert exc_info.value.quib is example_quib
    assert exc_info.value.override is override
    assert isinstance(str(exc_info.value), str)


def test_quib_override_allow_overriding_from_now_on(example_quib):
    example_quib.set_allow_overriding(False)
    override = Mock()
    override.path = [PathComponent(component=..., indexed_cls=example_quib.get_type())]

    example_quib.override(override, allow_overriding_from_now_on=True)

    assert example_quib._allow_overriding


@mark.regression
def test_remove_child_while_invalidating():
    class RemoveOnInvalidateQuib(ExampleQuib):
        def __init__(self, parent):
            super().__init__(None)
            parent.add_child(self)
            self._parent = parent

        @property
        def parents(self) -> Set[Quib]:
            return {self._parent}

        def _invalidate_self(self, path: List[PathComponent]):
            for parent in self.parents:
                parent.remove_child(self)

    parent = ExampleQuib([1])
    child = RemoveOnInvalidateQuib(parent)

    parent[0] = 1


@pytest.fixture
def parent(example_quib):
    parent = ExampleQuib(['parent', 'paren', 'par'])
    parent.add_child(example_quib)
    example_quib.add_parent(parent)
    return parent


@pytest.fixture
def mock_child_of_example_quib(example_quib):
    mock_quib_child = mock.Mock(spec=Quib)
    mock_quib_child._get_children_recursively.return_value = set()
    example_quib.add_child(mock_quib_child)
    return mock_quib_child


@pytest.mark.parametrize("assigned_path,invalidate_path,expected_to_have_invalidated_child", [
    ([0, 1], [0], True),
    ([0], [0], False),
    ([1], [0], True),
    ([0], [0, 1], False),
    ([1], [0, 1], True),
])
def test_quib_should_invalidate_children_when_overrides(example_quib, parent,
                                                                           mock_child_of_example_quib,
                                                                           assigned_path, invalidate_path,
                                                                           expected_to_have_invalidated_child):
    example_quib.assign(Assignment(path=[PathComponent(component=i, indexed_cls=list) for i in assigned_path],
                                   value=100))
    current_call_count = mock_child_of_example_quib._invalidate_quib_with_children_at_path.call_count

    parent.invalidate_and_redraw_at_path(path=[PathComponent(component=i, indexed_cls=list) for i in invalidate_path])

    new_expected_count = current_call_count if not expected_to_have_invalidated_child else current_call_count + 1
    assert mock_child_of_example_quib._invalidate_quib_with_children_at_path.call_count == new_expected_count


def test_quib_var_name():
    # we can't use examplequib as it's not a part of pyquibbler, and we only filter out pyquibbler frames
    my_quib = iquib(1)
    assert my_quib.name == "my_quib"


def test_quib_with_set_name():
    my_quib = iquib(1)
    name = "hello quib"

    my_quib.set_name(name)

    assert my_quib.name == name


def test_quib_with_multiple_in_same_line():
    a, b = iquib(1), iquib(2)

    assert a.name == 'a'
    assert b.name == 'b'


def test_quib_pretty_repr_with_quibs_being_created_inline():
    a = iquib([1, 2, 3])
    b, c = a[0], iquib(2)

    assert b.pretty_repr() == 'b = a[0]'
    assert c.pretty_repr() == 'c = iquib(2)'


@mark.regression
def test_quib_pretty_repr_with_quibs_with_quib_creation_with_name_in_inner_func():

    @quibbler_user_function(lazy=False)
    def inner_func():
        d = iquib(4)

        assert d.pretty_repr() == 'd = iquib(4)'

        return d

    @quibbler_user_function(lazy=False)
    def another_inner_func():
        e = iquib(4)

        assert e.pretty_repr() == 'e = iquib(4)'

        return e

    a, b = inner_func(), another_inner_func()

    assert a.pretty_repr() == 'a = inner_func()'
    assert b.pretty_repr() == 'b = another_inner_func()'


@mark.regression
def test_quib_pretty_repr_with_repr_throwing_exception():
    class A:
        def __repr__(self):
            raise Exception()

    quib = iquib(A())
    assert quib.pretty_repr() == "quib = [exception during repr]"


def test_quib_must_assign_bool_to_overriding(example_quib):
    with pytest.raises(InvalidArgumentException):
        example_quib.set_allow_overriding(1)


def test_quib_cannot_assign_int_to_name(example_quib):
    with pytest.raises(InvalidArgumentException):
        example_quib.set_name(1)


def test_quib_can_assign_none_to_name(example_quib):
    a = iquib(["val"])
    assert a.name == 'a', "Sanity check"

    example_quib.set_name(None)

    assert example_quib.name is None


def test_quib_configure(example_quib):
    quib = example_quib.setp(allow_overriding=True, name="pasten")

    assert quib.name == 'pasten'
    assert quib.allow_overriding is True


def test_quib_configure_with_invalid_value(example_quib):
    with pytest.raises(InvalidArgumentException):
        example_quib.setp(allow_overriding=3, name="pasten")


def test_quib_fails_when_given_invalid_assignment_on_first_get_value(example_quib):
    example_quib.assign_value_to_key(key=4, value=1)

    with pytest.raises(FailedToDeepAssignException):
        example_quib.get_value()


def test_quib_fails_when_not_matching_assignment_template():
    quib = ExampleQuib([1, 2, 3])
    quib.set_assignment_template(1, 3)
    quib.assign_value_to_key(key=2, value="hello johnny")

    with pytest.raises(InvalidTypeException):
        quib.get_value()


def test_iquib_does_not_fail_when_assignment_fails_on_second_get_value(example_quib):
    example_quib.assign_value_to_key(key=2, value=1)
    example_quib.get_value()
    example_quib.assign_value([1])

    # just make sure we don't fail
    example_quib.get_value()
