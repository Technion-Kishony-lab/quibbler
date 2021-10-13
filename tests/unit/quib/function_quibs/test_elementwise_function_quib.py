import numpy as np

from pyquibbler import iquib
from pyquibbler.quib.assignment.assignment import PathComponent


def test_elementwise_function_quib_invalidation_when_should_invalidate():
    a = iquib(np.array([1, 2, 3]))
    b = a + 1
    b.get_value()

    a.invalidate_and_redraw_at_path(path=[PathComponent(
        component=0,
        indexed_cls=list
    )])

    assert not b.is_cache_valid


def test_elementwise_function_quib_invalidation_when_should_not_invalidate():
    a = iquib(np.array([[1, 2, 3]]))
    b = iquib(np.array([[1], [2], [3]]))
    sum_ = a + b
    item = sum_[(2, 0)]
    item.get_value()

    a.invalidate_and_redraw_at_path(path=[PathComponent(
        component=(0, 0),
        indexed_cls=list
    )])

    assert not item.is_cache_valid


def test_elementwise_function_quib_invalidation_at_field_does_nothing():
    dtype = [('inteliggence', np.int_), ('age', np.int_)]
    a = iquib(np.array([(100, 24)], dtype=dtype))
    b = a['age'] + 1
    b.get_value()
    
    a.invalidate_and_redraw_at_path(path=[PathComponent(
        component='age',
        indexed_cls=np.ndarray
    )])

    assert not b.is_cache_valid