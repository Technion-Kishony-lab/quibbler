import magicmethods
import operator
from unittest.mock import Mock
from pytest import mark, raises
from unittest import mock
from pytest import fixture

from pyquibbler.quib import Quib
from pyquibbler.quib.assignment_template import RangeAssignmentTemplate, BoundAssignmentTemplate
from pyquibbler.quib.graphics import GraphicsFunctionQuib


class ExampleQuib(Quib):
    def __init__(self, value, assignment_template=None):
        super().__init__(assignment_template=assignment_template)
        self.value = value
        self.invalidate_count = 0

    def _invalidate(self):
        self.invalidate_count += 1

    def get_value(self):
        return self.value

    def _override(self, key, value):
        self.value[key] = value


@fixture
def assignment_template_mock():
    mock = Mock()
    mock.convert.return_value = object()
    return mock


@fixture
def example_quib(assignment_template_mock):
    return ExampleQuib(['the', 'quib', 'value'], assignment_template=assignment_template_mock)


def test_quib_getitem(example_quib):
    got = example_quib[0]

    assert got.get_value() is example_quib.value[0]


def test_quib_getattr_with_class_attr(example_quib):
    got = example_quib.sort

    assert got.get_value() == example_quib.value.sort


def test_quib_getattr_with_instance_attr():
    quib = ExampleQuib(type('_', (), dict(attr='value')))
    got = quib.attr
    assert got.get_value() == quib.value.attr


def test_call_quib_method(example_quib):
    assert example_quib.index(example_quib.value[1]).get_value() == 1


def test_quib_invalidate_and_redraw_calls_graphics_function_quib_children(example_quib):
    mock_func = mock.Mock()
    mock_func.return_value = []
    quib = GraphicsFunctionQuib(func=mock_func, args=tuple(), kwargs={}, artists=[], cache_behavior=None)
    example_quib.add_child(quib)

    example_quib.invalidate_and_redraw()

    mock_func.assert_called_once()


def test_quib_call():
    expected_args = (2, 'args')
    expected_kwargs = dict(name='val')
    expected_result = 'the result'

    def wrapped_func(*args, **kwargs):
        assert expected_args == args
        assert expected_kwargs == kwargs
        return expected_result

    quib = ExampleQuib(wrapped_func)
    call_quib = quib(*expected_args, **expected_kwargs)
    result = call_quib.get_value()

    assert result is expected_result


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


def test_quib_setitem_without_assignment_template():
    quib = ExampleQuib(['old item'])
    new_item = 'new item'
    quib[0] = new_item

    assert quib.get_value()[0] is new_item


def test_quib_setitem_uses_assignment_template(example_quib, assignment_template_mock):
    example_quib[0] = 'val'

    assignment_template_mock.convert.assert_called_once_with('val')
    assert example_quib[0].get_value() is assignment_template_mock.convert.return_value
