import pytest

from pyquibbler import iquib
from pyquibbler.refactor.env import PRETTY_REPR


@pytest.fixture
def a():
    a = iquib(1)
    return a


@pytest.fixture
def b():
    b = iquib(1)
    return b


@pytest.fixture
def c():
    c = iquib(1)
    return c


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_math_unary_operator():
    a = iquib(1)
    c = -a

    assert c.pretty_repr() == 'c = -a'


@pytest.mark.parametrize("statement,expected", [
    ("a * b + c", "a * b + c"),
    ("a * (b + c)", "a * (b + c)"),
    ("(a * b) + c", "a * b + c"),
    ("a / (b * c) * a", "a / (b * c) * a"),
    ("a + b + c", "a + b + c"),
    ("a ** (b / (c + a))", "a ** (b / (c + a))"),
    ("a - (b + c)", "a - (b + c)"),
    ("a / (b / c)", "a / (b / c)"),
    ("a // (b // c)", "a // (b // c)"),
    ("a @ (b + c)", "a @ (b + c)"),
    ("a < b + c", "a < b + c"),
    ("a + b <= c", "c >= a + b"),
    ("(a < b) < c", "(a < b) < c"),
    ("a < (b < c)", "a < (b < c)"),
    ("-a", "-a"),
    ("--a", "--a"),
    ("-a * b", "-a * b"),
    ("-b + a", "-b + a"),
    ("a | b & c", "a | b & c"),
    ("(a | b) & c", "(a | b) & c"),
    ("a | b | c", "a | b | c"),
])
@pytest.mark.get_variable_names(True)
def test_function_quib_pretty_repr_math_holds_pemdas(a, b, c, statement, expected):
    with PRETTY_REPR.temporary_set(True):
        assert repr(eval(statement)) == expected
