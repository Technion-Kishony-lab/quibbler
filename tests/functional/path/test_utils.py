import numpy as np
import pytest

from pyquibbler.path import Path, PathComponent, split_path_at_end_of_object, SpecialComponent
from pyquibbler.path.data_accessing import de_array_by_template, deep_set
from pyquibbler.utilities.iterators import recursively_compare_objects


def ndcmp(cmp) -> PathComponent:
    return PathComponent(cmp)


@pytest.mark.parametrize('path,obj,expected_within,expected_after', [
    [[ndcmp(1), ndcmp(2)], np.array([1, 2, 3]), [ndcmp(1)], [ndcmp(2)]],
    [[ndcmp((1, 2))], np.array([1, 2, 3]), [ndcmp((1,))], [ndcmp((2,))]],
    [[ndcmp(1), ndcmp(2)], np.zeros((2, 3)), [ndcmp(1), ndcmp(2)], []],
    [[ndcmp(1), ndcmp(2), ndcmp(0)], np.zeros((2, 3)), [ndcmp(1), ndcmp(2)], [ndcmp(0)]],
    [[ndcmp((1, 2)), ndcmp(0)], np.zeros((2, 3)), [ndcmp((1, 2))], [ndcmp(0)]],
    [[ndcmp((1, 2, 0))], np.zeros((2, 3)), [ndcmp((1, 2))], [ndcmp((0,))]],
    [[ndcmp(([1], [2]))], np.zeros((2, 3)), [ndcmp(([1], [2]))], []],
])
def test_split_path_at_end_of_object(path, obj, expected_within, expected_after):
    within, after, _ = split_path_at_end_of_object(obj, path)
    assert recursively_compare_objects(within, expected_within)
    assert recursively_compare_objects(after, expected_after)


@pytest.mark.parametrize('obj', [
    [1, 2.5],
    [[1, 2], [3, 4]],
    [[1, 2], np.array([3, 4])],
])
def test_de_array_by_template(obj):
    array = np.array(obj, dtype=object)
    de_array = de_array_by_template(array, obj)
    recursively_compare_objects(de_array, obj)


PC = PathComponent


@pytest.mark.parametrize('obj, path, value, expected', [
    ([1, 2, 3], [PC(1)], 'roy', [1, 'roy', 3]),
    ((1, 2, 3), [PC(1)], 'roy', (1, 'roy', 3)),
    (np.array([1, 2, 3]), [PC([False, True, False])], 7, np.array([1, 7, 3])),
    (np.array([{'num': 1}, {'num': 2}, {'num': 3}]), [PC(1), PC('num')], 7, np.array([{'num': 1}, {'num': 7}, {'num': 3}])),
    (np.array([{'num': 1}, {'num': 2}, {'num': 3}]), [PC([False, True, False]), PC(SpecialComponent.OUT_OF_ARRAY), PC('num')], 7, np.array([{'num': 1}, {'num': 7}, {'num': 3}])),
])
def test_deep_set(obj, path, value, expected):
    obj = deep_set(obj, path, value)
    assert recursively_compare_objects(obj, expected)
