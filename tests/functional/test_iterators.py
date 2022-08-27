import unittest

import numpy as np
import pytest
from pyquibbler.utilities.iterators import recursively_cast_one_object_by_other, recursively_compare_objects, \
    CannotCastObjectByOtherObjectException


@pytest.mark.parametrize(['template', 'obj', 'expected'], [
    ([1, 2., {'a': 'abc', 'b': 10}, np.array([1, 2, 3])],
     [1.1, 3, {'a': 25, 'b': 12.3}, np.array([[2., 10.], [1, 3]])],
     [1, 3., {'a': '25', 'b': 12}, np.array([[2, 10], [1, 3]])]),

    (1, 2.7, 3),

    (np.array([0, 0, 0], dtype=np.short), np.array([1, 3]), np.array([1, 3], dtype=np.short)),
    (np.array([0, 0, 0], dtype=object), np.array([1, 3]), CannotCastObjectByOtherObjectException),
    (np.array([0, [1]], dtype=object), np.array([1.2, [3.2]], dtype=object), np.array([1, [3]], dtype=object)),
    ([1, 2], [1, 2, 3], CannotCastObjectByOtherObjectException),
    ({'a': 2}, 7, CannotCastObjectByOtherObjectException),
])
def test_recursively_cast_one_object_by_other(template, obj, expected):
    if isinstance(expected, type(Exception)):
        with pytest.raises(expected, match='.*'):
            recursively_cast_one_object_by_other(template, obj)
    else:
        casted_obj = recursively_cast_one_object_by_other(template, obj)
        assert recursively_compare_objects(casted_obj, expected, type_only=True)


def test_recursively_compare_objects_type():
    obj1 = [1, 2., {'a': 'abc', 'b': 10}, np.array([1, 2, 3])]
    obj2 = [1, 3., {'a': 'XX', 'b': 12}, np.array([[100]])]

    assert recursively_compare_objects(obj1, obj2, type_only=True)
    assert not recursively_compare_objects(obj1, obj2, type_only=False)

