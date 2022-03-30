import numpy as np
from operator import or_
from functools import reduce
from typing import Set

from pyquibbler import iquib, CacheMode
from pyquibbler.quib.quib import Quib
from pyquibbler.cache.cache import CacheStatus


def breakdown_quib(quib: Quib) -> Set[Quib]:
    quib_type = quib.get_type()
    if issubclass(quib_type, np.ndarray):
        return {quib[idx] for idx in np.ndindex(quib.get_shape())}
    if issubclass(quib_type, (np.generic, int)):
        return set()
    if issubclass(quib_type, (tuple, list)):
        return reduce(or_, (breakdown_quib(sub_quib) for sub_quib in quib.iter_first(len(quib.get_value()))))
    raise TypeError(f'Unsupported quib type: {quib_type}')


def get_indices_from_getitem_quibs(getitem_quibs):
    return sorted(c.args[1] if len(c.args[1]) != 1 else c.args[1][0] for c in getitem_quibs)


def check_invalidation(func, data, indices_to_invalidate):
    """
    Run func on an ndarray iquib, change the iquib in the given indices,
    and verify that the invalidated children were also the ones that changed values.
    Make sure that func works in a way that guarantees that when a value in the input changes,
    all affected values in the result also change.
    """
    input_quib = iquib(data)
    result = func(input_quib)
    result.cache_mode = CacheMode.OFF
    children = breakdown_quib(result)

    original_values = {child: child.get_value() for child in children}
    input_quib[indices_to_invalidate] = 999

    invalidated_children = {child for child in children if child.cache_status == CacheStatus.ALL_INVALID}
    changed_children = {child for child in children if not np.array_equal(child.get_value(), original_values[child])}
    assert invalidated_children == changed_children, \
        f'\nInvalidated: {get_indices_from_getitem_quibs(invalidated_children)}' \
        f'\nExpected:    {get_indices_from_getitem_quibs(changed_children)}'
