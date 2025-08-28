import unittest

import numpy as np
import pytest
from pyquibbler.utilities.iterators import recursively_compare_objects


def test_recursively_compare_objects_type():
    obj1 = [1, 2., {'a': 'abc', 'b': 10}, np.array([1, 2, 3])]
    obj2 = [1, 3., {'a': 'XX', 'b': 12}, np.array([[100]])]

    assert recursively_compare_objects(obj1, obj2, type_only=True)
    assert not recursively_compare_objects(obj1, obj2, type_only=False)

