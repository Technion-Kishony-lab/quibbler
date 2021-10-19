import numpy as np

from pyquibbler import iquib
from pyquibbler.quib.assignment.assignment import PathComponent


def test_elementwise_function_quib_invalidation_with_flat_list():
    a = iquib([1, 2])
    b = np.add(a, 1)
    c = b[0]
    c.get_value()
    d = b[1]
    d.get_value()

    a.invalidate_and_redraw_at_path(path=[PathComponent(
        component=0,
        indexed_cls=list
    )])

    assert not c.is_cache_valid
    assert d.is_cache_valid


def test_elementwise_function_quib_invalidation_with_broadcast_numpy_array():
    a = iquib(np.array([[1, 2]]))
    b = iquib(np.array([[1], [2]]))
    sum_ = a + b
    indices = [(0, 0), (0, 1), (1, 0), (1, 1)]
    should_be_invalidated_list = [True, False, True, False]
    quibs = [sum_[i] for i in indices]
    for quib in quibs:
        quib.get_value()

    a.invalidate_and_redraw_at_path(path=[PathComponent(
        component=(0, 0),
        indexed_cls=np.ndarray
    )])

    for quib, should_be_invalidated in zip(quibs, should_be_invalidated_list):
        assert quib.is_cache_valid == (not should_be_invalidated)


def test_elementwise_function_quib_invalidation_at_field_invalidates():
    dtype = [('inteliggence', np.int_), ('age', np.int_)]
    a = iquib(np.array([(100, 24)], dtype=dtype))
    b = a['age'] + 1
    b.get_value()

    a.invalidate_and_redraw_at_path(path=[PathComponent(
        component='age',
        indexed_cls=np.ndarray
    )])

    assert not b.is_cache_valid
