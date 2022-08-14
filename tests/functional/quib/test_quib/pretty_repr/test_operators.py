import pytest

from pyquibbler import iquib
from pyquibbler.env import PRETTY_REPR


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

    assert c.pretty_repr == 'c = -a'


@pytest.mark.parametrize("statement,expected", [
    ("a*a*a + b", None),
    ("a*b + c", None),
    ("a * (b + c)", None),
    ("(a * b) + c", "a*b + c"),
    ("a / (b * c) * a", None),
    ("a + b + c", None),
    ("a * b * c", None),
    ("a / b * c", None),
    ("a ** (b / (c + a))", None),
    ("a + b**c", None),
    ("a + a / b**c", None),
    ("a - (b + c)", None),
    ("a / (b / c)", None),
    ("a // (b // c)", None),
    ("a @ (b + c)", None),
    ("a < b+c", None),
    ("a+b <= c", None),
    ("(a < b) < c", None),
    ("a < (b < c)", None),
    ("~a", None),
    ("-a", None),
    ("--a", None),
    ("-a * b", None),
    ("-b + a", None),
    ("a | b&c", None),
    ("(a | b) & c", None),
    ("a | b | c", None),
    ("a + None", None),
    ("a + 'hello'", None),
    ("'hello' + a", None),
    ("10 / a", None),
    ("5 - (10 + a)", None),
])
@pytest.mark.get_variable_names(True)
def test_function_quib_pretty_repr_math_holds_pemdas(a, b, c, statement, expected):
    expected = expected or statement
    with PRETTY_REPR.temporary_set(True):
        assert repr(eval(statement)) == expected
