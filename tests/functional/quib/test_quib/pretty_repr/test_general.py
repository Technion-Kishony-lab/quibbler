import numpy as np
import pytest

from pyquibbler.quib.specialized_functions.iquib import iquib
from pyquibbler.decorators import quibbler_user_function
from pyquibbler.utilities.user_utils import q


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_with_quibs_being_created_inline():
    a = iquib([1, 2, 3])
    b, c = a[0], iquib(2)

    assert b.pretty_repr() == 'b = a[0]'
    assert c.pretty_repr() == 'c = iquib(2)'


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_with_quibs_with_quib_creation_with_name_in_inner_func():
    @quibbler_user_function(evaluate_now=True)
    def inner_func():
        d = iquib(4)
        return d

    @quibbler_user_function(evaluate_now=True)
    def another_inner_func():
        e = iquib(4)
        return e

    a, b = inner_func(), another_inner_func()

    assert a.pretty_repr() == 'a = inner_func()'
    assert b.pretty_repr() == 'b = another_inner_func()'


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_with_repr_throwing_exception():
    class A:
        def __repr__(self):
            raise Exception()

    quib = iquib(A())
    assert quib.pretty_repr() == "quib = [exception during repr]"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_without_name():
    a = iquib(1)
    b = iquib(2)

    assert q("".join, [a, b]).pretty_repr() == 'join([a, b])'


@pytest.mark.parametrize("statement", [
    "a[:]",
    "a[1:2:3]",
    "a[1::2]",
    "a[::2]",
    "a[:2]",
    "a[1:]"
])
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_colon(statement):
    a = iquib(np.array([1, 2, 3]))
    b = eval(statement)

    assert b.pretty_repr() == statement


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_set():
    a = iquib({0})

    assert a.pretty_repr() == "a = iquib({0})"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_none():
    a = iquib([None])

    assert a.pretty_repr() == "a = iquib([None])"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_dict():
    a = iquib(1)
    b = q(str, {'data': a, 'num': 2, 1.0: 'b'})

    assert b.pretty_repr() == "b = str({'data': a, 'num': 2, 1.0: 'b'})"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_ellipsis():
    a = iquib(np.array([1, 2, 3]))
    b = a[...]

    assert b.pretty_repr() == "b = a[...]"


@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_getitem_index():
    a = iquib(np.array([1, 2, 3]))
    b = a[1]

    assert b.pretty_repr() == "b = a[1]"


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_quib_pretty_repr_on_q_with_dict():
    x = iquib(3)

    assert q(dict, ('num', x)).pretty_repr() == "dict(('num', x))"


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_getitem_pretty_repr_with_quib_as_item():
    a = iquib([1, 2, 3])
    b = iquib(1)

    assert a[:b].pretty_repr() == 'a[:b]'