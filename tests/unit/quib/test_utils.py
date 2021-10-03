from operator import add

from pytest import mark, raises

from pyquibbler import iquib
from pyquibbler.quib import Quib
from pyquibbler.quib.utils import is_iterator_empty, deep_copy_and_replace_quibs_with_vals, \
    iter_objects_of_type_in_object_recursively, call_func_with_quib_values, iter_quibs_in_args, \
    is_there_a_quib_in_args, NestedQuibException, copy_and_replace_quibs_with_vals, iter_quibs_in_object, \
    FunctionCalledWithNestedQuibException, QuibRef

iquib1 = iquib(1)
iquib2 = iquib(2)


@mark.parametrize(['iterator', 'expected_result'], [
    (iter([]), True),
    (iter([1]), False),
])
def test_is_iterator_empty(iterator, expected_result):
    assert is_iterator_empty(iterator) == expected_result


@mark.parametrize(['to_copy', 'depth', 'length', 'expected_result'], [
    ([1, [2]], None, None, [1, [2]]),
    ([1, [2]], 0, 0, [1, [2]]),
    ([1, [2]], 1, 10, [1, [2]]),
    ([1, [2]], 5, 10, [1, [2]]),
    (iquib1, None, None, 1),
    (iquib1, 0, 0, 1),
    (iquib1, 3, 3, 1),
    ([iquib1], None, None, [1]),
    ([iquib1], 0, None, [iquib1]),
    ([iquib1], 1, None, [1]),
    ([iquib1], 2, None, [1]),
    ([iquib1], None, 0, [iquib1]),
    ([iquib1], None, 1, [1]),
    ([1, [iquib1, [iquib2]]], None, None, [1, [1, [2]]]),
    ([1, [iquib1, [iquib2]]], 0, None, [1, [iquib1, [iquib2]]]),
    ([1, [iquib1, [iquib2]]], 1, None, [1, [iquib1, [iquib2]]]),
    ([1, [iquib1, [iquib2]]], 2, None, [1, [1, [iquib2]]]),
    ([1, [iquib1, [iquib2]]], 3, None, [1, [1, [2]]]),
    ([1, [iquib1, [iquib2]]], None, 0, [1, [iquib1, [iquib2]]]),
    ([1, [iquib1, [iquib2]]], None, 1, [1, [iquib1, [iquib2]]]),
    ([1, [iquib1, [iquib2]]], None, 2, [1, [1, [2]]]),
    ([QuibRef(iquib1)], None, None, [iquib1]),
])
def test_deep_copy_and_replace_quibs_with_vals(to_copy, depth, length, expected_result):
    assert deep_copy_and_replace_quibs_with_vals(to_copy, depth, length) == expected_result


@mark.parametrize(['to_iter', 'depth', 'length', 'expected_result'], [
    ([1, [2]], None, None, set()),
    ([1, [2]], 0, 0, set()),
    ([1, [2]], 0, 1, set()),
    ([1, [2]], 0, 2, set()),
    ([1, [2]], 10, 0, set()),
    (iquib1, None, None, {iquib1}),
    (iquib1, 0, 0, {iquib1}),
    (iquib1, 3, 3, {iquib1}),
    ([iquib1], None, None, {iquib1}),
    ([iquib1, iquib1, iquib2], None, None, {iquib1, iquib2}),
    ([iquib1], 0, None, set()),
    ([iquib1], 1, None, {iquib1}),
    ([iquib1], 2, None, {iquib1}),
    ([iquib1], None, 0, set()),
    ([iquib1], None, 1, {iquib1}),
    ([1, [iquib1, [iquib2]]], None, None, {iquib1, iquib2}),
    ([1, [iquib1, [iquib2]]], 0, None, set()),
    ([1, [iquib1, [iquib2]]], 1, None, set()),
    ([1, [iquib1, [iquib2]]], 2, None, {iquib1}),
    ([1, [iquib1, [iquib2]]], 3, None, {iquib1, iquib2}),
    ([1, [iquib1, [iquib2]]], None, 0, set()),
    ([1, [iquib1, [iquib2]]], None, 1, set()),
    ([1, [iquib1, [iquib2]]], None, 2, {iquib1, iquib2}),
    ([QuibRef(iquib1)], None, None, {iquib1}),
])
def test_iter_quibs_in_object(to_iter, depth, length, expected_result):
    assert set(iter_objects_of_type_in_object_recursively(Quib, to_iter, depth, length)) == expected_result


@mark.parametrize(['func', 'args', 'kwargs', 'result'], [
    (add, (1, 1), dict(), 2),
    (add, (1, iquib1), dict(), 2),
    (add, (iquib1, iquib1), dict(), 2),
    (lambda x, y: x + y[0], (1, [iquib1]), dict(), 2),
    (lambda x, y: x + y, (1,), dict(y=1), 2),
])
def test_call_func_with_quib_values(func, args, kwargs, result):
    assert call_func_with_quib_values(func, args, kwargs) == result


@mark.debug(False)
def test_call_func_with_quib_values_raises_when_receives_nested_quib():
    obj = [[iquib1]]
    func = lambda x: open(x[0][0])
    with raises(FunctionCalledWithNestedQuibException) as exc_info:
        call_func_with_quib_values(func, (obj,), {})
    assert exc_info.type is FunctionCalledWithNestedQuibException
    assert exc_info.value.func == func
    assert exc_info.value.nested_quibs_by_arg_names == {'x': {iquib1}}
    assert isinstance(exc_info.value.__cause__, TypeError)


args_kwargs_quibs_test = mark.parametrize(['args', 'kwargs', 'quibs'], [
    ((), dict(), set()),
    ((1,), dict(a=1), set()),
    ((iquib1,), dict(a=1), {iquib1}),
    ((iquib1,), dict(a=iquib2), {iquib1, iquib2}),
    ((), dict(a=[iquib2]), {iquib2}),
])


@args_kwargs_quibs_test
def test_iter_quibs_in_args(args, kwargs, quibs):
    assert set(iter_quibs_in_args(args, kwargs)) == quibs


@args_kwargs_quibs_test
def test_is_there_a_quib_in_args(args, kwargs, quibs):
    assert is_there_a_quib_in_args(args, kwargs) == (len(quibs) > 0)


def test_copy_and_replace_quibs_with_vals_raises_when_receives_nested_quibs():
    obj = [[iquib1]]
    with raises(NestedQuibException) as exc_info:
        copy_and_replace_quibs_with_vals(obj)

    assert exc_info.type is NestedQuibException
    assert exc_info.value.obj is obj
    assert exc_info.value.nested_quibs == {iquib1}


def test_iter_quibs_in_object_raises_when_receives_nested_quibs():
    obj = [[iquib1]]
    with raises(NestedQuibException) as exc_info:
        iter_quibs_in_object(obj)

    assert exc_info.type is NestedQuibException
    assert exc_info.value.obj is obj
    assert exc_info.value.nested_quibs == {iquib1}
