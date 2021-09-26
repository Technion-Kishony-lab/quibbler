import magicmethods
import operator
from unittest.mock import Mock
from pytest import fixture, mark
from unittest import mock

from pytest import fixture

from pyquibbler.quib import Quib


class ExampleQuib(Quib):
    def __init__(self, value, invalidate_func=None):
        super().__init__()
        self.value = value
        self._invalidate = invalidate_func

    def _invalidate(self):
        pass

    def get_value(self):
        return self.value



@fixture
def example_quib():
    return ExampleQuib(['the', 'quib', 'value'])


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
    from pyquibbler.quib.graphics import GraphicsFunctionQuib
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


def test_quib_children_automatically():
    quib = ExampleQuib('something')
    child = ExampleQuib('child')
    child_invalidate = child._invalidate = Mock()
    quib.add_child(child)
    del child
    quib.invalidate_and_redraw()

    child_invalidate.assert_not_called()


def test_quib_invalidates_children_recursively(example_quib):
    # Regression test
    child_invalidate = mock.Mock()
    child = ExampleQuib(value=mock.Mock(), invalidate_func=child_invalidate)
    child._invalidate = child_invalidate
    grandchild_invalidate = mock.Mock()
    grandchild = ExampleQuib(value=mock.Mock(),invalidate_func=grandchild_invalidate)
    example_quib.add_child(child)
    child.add_child(grandchild)

    example_quib.invalidate_and_redraw()

    child_invalidate.assert_called_once()
    grandchild_invalidate.assert_called_once()
