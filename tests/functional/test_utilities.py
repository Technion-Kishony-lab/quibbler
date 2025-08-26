from dataclasses import dataclass
from typing import Tuple

from pytest import mark, raises, fixture

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.specialized_functions.iquib import create_iquib
from pyquibbler.quib.utils.iterators import iter_quibs_in_object
from pyquibbler.quib.utils.miscellaneous import deep_copy_without_graphics
from pyquibbler.utilities.iterators import is_iterator_empty, iter_objects_of_type_in_object_recursively
from pyquibbler.utilities.unpacker import Unpacker, CannotDetermineNumberOfIterations
from tests.functional.utils import slicer


iquib1 = create_iquib(1)
iquib2 = create_iquib(2)


@mark.parametrize(['iterator', 'expected_result'], [
    (iter([]), True),
    (iter([1]), False),
])
def test_is_iterator_empty(iterator, expected_result):
    assert is_iterator_empty(iterator) == expected_result


@mark.parametrize(['to_copy', 'expected_result'], [
    (iquib1, 1),
])
@mark.debug(False)
def test_copy_and_replace_quibs_with_vals(monkeypatch, to_copy, expected_result):
    assert deep_copy_without_graphics(to_copy, action_on_quibs='value') == expected_result


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
    (slicer[iquib1:, iquib1:iquib2], 2, None, {iquib1, iquib2}),
    (dict(b=[iquib2], c=dict(d=1, e=iquib1)), None, None, {iquib1, iquib2}),
])
def test_iter_quibs_in_object(to_iter, depth, length, expected_result):
    assert set(iter_objects_of_type_in_object_recursively(Quib, to_iter, depth, length)) == expected_result


args_kwargs_quibs_test = mark.parametrize(['args', 'kwargs', 'quibs'], [
    ((), dict(), set()),
    ((1,), dict(a=1), set()),
    ((iquib1,), dict(a=1), {iquib1}),
    ((iquib1,), dict(a=iquib2), {iquib1, iquib2}),
    ((), dict(a=[iquib2]), {iquib2}),
])


@fixture
def unpacker_value():

    @dataclass
    class NoLenIter:
        value: Tuple

        def __getitem__(self, item):
            return self.value[item]

    return NoLenIter((1, 2, 3))


@fixture
def unpacker(unpacker_value):
    return Unpacker(unpacker_value)


@fixture
def unpacker_with_set_length(unpacker_value):
    return Unpacker(unpacker_value, len(unpacker_value.value))


def test_unpacker_with_normal_unpack_of_one(unpacker, unpacker_value):
    a, = unpacker

    assert a == unpacker_value[0]


def test_unpacker_with_normal_unpack_of_two(unpacker, unpacker_value):
    a, b = unpacker

    assert (a, b) == unpacker_value[:2]


def test_unpacker_with_normal_unpack_of_three(unpacker, unpacker_value):
    a, b, c = unpacker

    assert (a, b, c) == unpacker_value[:3]


def test_unpacker_with_tuple_unpack(unpacker, unpacker_value):
    (a, b, c) = unpacker

    assert (a, b, c) == unpacker_value[:3]


def test_unpacker_with_list_unpack(unpacker, unpacker_value):
    [a, b, c] = unpacker

    assert (a, b, c) == unpacker_value[:3]


def test_unpacker_after_iter(unpacker, unpacker_value):
    unpacker = iter(unpacker)
    a, b, c = unpacker

    assert (a, b, c) == unpacker_value[:3]


def test_unpacker_after_next(unpacker, unpacker_value):
    a = next(unpacker)
    b, c = unpacker

    assert (a, b, c) == unpacker_value[:3]


def test_unpacker_raises_with_star_unpack(unpacker):
    with raises(CannotDetermineNumberOfIterations):
        a, *b = unpacker


def test_unpacker_raises_when_unpacking_too_much(unpacker):
    with raises(ValueError) as e:
        a, b, c, d = unpacker
    assert e.value.args == ('not enough values to unpack (expected 4, got 3)',)


def test_unpacker_with_set_length_unpacks(unpacker_with_set_length, unpacker_value):
    a, b, c = unpacker_with_set_length

    assert (a, b, c) == unpacker_value[:3]


def test_unpacker_with_set_length_fails_on_too_little(unpacker_with_set_length, unpacker_value):
    with raises(ValueError) as e:
        a, b = unpacker_with_set_length
    assert e.value.args == ('too many values to unpack (expected 2)',)


def test_unpacker_with_set_length_fails_on_too_much(unpacker_with_set_length, unpacker_value):
    with raises(ValueError) as e:
        a, b, c, d = unpacker_with_set_length
    assert e.value.args == ('not enough values to unpack (expected 4, got 3)',)
