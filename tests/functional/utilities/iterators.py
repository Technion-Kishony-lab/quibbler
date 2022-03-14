import numpy as np

from pyquibbler.utilities.iterators import recursively_cast_one_object_by_other, recursively_compare_objects_type


def test_recursively_cast_one_object_by_other():
    template = [1, 2., {'a': 'abc', 'b': 10}, np.array([1, 2, 3])]
    obj = [1.1, 3, {'a': 25, 'b': 12.3}, np.array([[2., 10.], [1, 3]])]

    obj = recursively_cast_one_object_by_other(template, obj)
    assert recursively_compare_objects_type(obj,
                                            [1, 3., {'a': '25', 'b': 12}, np.array([[2, 10], [1, 3]])])


def test_recursively_compare_objects_type():
    obj1 = [1, 2., {'a': 'abc', 'b': 10}, np.array([1, 2, 3])]
    obj2 = [1, 3., {'a': 'XX', 'b': 12}, np.array([[100]])]

    assert recursively_compare_objects_type(obj1, obj2, type_only=True)
    assert not recursively_compare_objects_type(obj1, obj2, type_only=False)

