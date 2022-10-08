import numpy as np
import pytest

from pyquibbler.path import Path, PathComponent, split_path_at_end_of_object
from pyquibbler.path.data_accessing import de_array_by_template
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
