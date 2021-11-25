import pytest

from pyquibbler import quibbler_user_function
from pyquibbler.quib.refactor.iquib import iquib


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

