from operator import add

from pytest import mark

from pyquibbler import iquib
from pyquibbler.quib.utils import is_iterator_empty, deep_copy_and_replace_quibs_with_vals, iter_quibs_in_object, \
    call_func_with_quib_values, iter_quibs_in_args, \
    is_there_a_quib_in_args

iquib1 = iquib(1)
iquib2 = iquib(2)


@mark.parametrize(['iterator', 'expected_result'], [
    (iter([]), True),
    (iter([1]), False),
])
def test_is_iterator_empty(iterator, expected_result):
    assert is_iterator_empty(iterator) == expected_result


@mark.parametrize(['to_copy', 'expected_result'], [
    ([1, [2]], [1, [2]]),
    (iquib1, 1),
    ([iquib1], [1]),
    ([1, [iquib1, [iquib2]]], [1, [1, [2]]]),
])
def test_deep_copy_and_replace_quibs_with_vals(to_copy, expected_result):
    assert deep_copy_and_replace_quibs_with_vals(to_copy) == expected_result


@mark.parametrize(['to_iter', 'expected_result'], [
    ([1, [2]], set()),
    (None, set()),
    (iquib1, {iquib1}),
    ([1, [iquib1, iquib2], iquib1], {iquib1, iquib2}),
])
def test_iter_quibs_in_object(to_iter, expected_result):
    assert set(iter_quibs_in_object(to_iter)) == expected_result


@mark.parametrize(['func', 'args', 'kwargs', 'result'], [
    (add, (1, 1), dict(), 2),
    (add, (1, iquib(1)), dict(), 2),
    (add, (iquib(1), iquib(1)), dict(), 2),
    (lambda x, y: x + y[0], (1, [iquib(1)]), dict(), 2),
    (lambda x, y: x + y[0][0], (1, [[iquib(1)]]), dict(), 2),
    (lambda x, y: x + y, (1,), dict(y=1), 2),
])
def test_call_func_with_quib_values(func, args, kwargs, result):
    assert call_func_with_quib_values(func, args, kwargs) == result


args_kwargs_quibs_test = mark.parametrize(['args', 'kwargs', 'quibs'], [
    ((), dict(), set()),
    ((1,), dict(a=1), set()),
    ((iquib1,), dict(a=1), {iquib1}),
    ((iquib1,), dict(a=iquib2), {iquib1, iquib2}),
    ((), dict(a=[(0, iquib2)]), {iquib2}),
])


@args_kwargs_quibs_test
def test_iter_quibs_in_args(args, kwargs, quibs):
    assert set(iter_quibs_in_args(args, kwargs)) == quibs


@args_kwargs_quibs_test
def test_is_there_a_quib_in_args(args, kwargs, quibs):
    assert is_there_a_quib_in_args(args, kwargs) == (len(quibs) > 0)
