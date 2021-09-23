import magicmethods
import operator
from pytest import fixture, mark

from pyquibbler.quib import Quib


class ExampleQuib(Quib):
    def __init__(self, artists_redrawers, children, value):
        super().__init__(artists_redrawers, children)
        self.value = value

    def _invalidate(self):
        pass

    def get_value(self):
        return self.value

    @classmethod
    def create(cls, value):
        return cls(set(), [], value)


@fixture
def example_quib():
    return ExampleQuib.create(['the', 'quib', 'value'])


def test_quib_getitem(example_quib):
    got = example_quib[0]
    assert got.get_value() is example_quib.value[0]


def test_quib_getattr_with_class_attr(example_quib):
    got = example_quib.sort
    assert got.get_value() == example_quib.value.sort


def test_quib_getattr_with_instance_attr():
    quib = ExampleQuib.create(type('_', (), dict(attr='value')))
    got = quib.attr
    assert got.get_value() == quib.value.attr


def test_call_quib_method(example_quib):
    assert example_quib.index(example_quib.value[1]).get_value() == 1


def test_quib_call():
    expected_args = (2, 'args')
    expected_kwargs = dict(name='val')
    expected_result = 'the result'

    def wrapped_func(*args, **kwargs):
        assert expected_args == args
        assert expected_kwargs == kwargs
        return expected_result

    quib = ExampleQuib(set(), [], wrapped_func)
    call_quib = quib(*expected_args, **expected_kwargs)
    result = call_quib.get_value()

    assert result is expected_result


@mark.parametrize('operator_name', set(magicmethods.arithmetic) - {'__div__', '__divmod__'})
def test_quib_forward_and_reverse_binary_operators(operator_name: str):
    op = getattr(operator, operator_name, None)
    quib1 = ExampleQuib.create(1)
    quib2 = ExampleQuib.create(2)

    # Forward operators
    assert op(quib1, quib2).get_value() == op(quib1.value, quib2.value)
    assert op(quib1, quib2.value).get_value() == op(quib1.value, quib2.value)
    # Reverse operators
    assert op(quib1.value, quib2).get_value() == op(quib1.value, quib2.value)
