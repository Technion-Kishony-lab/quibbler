import numpy as np
from operator import or_
from functools import reduce
from typing import Set

from pyquibbler import iquib, CacheBehavior
from pyquibbler.quib import Quib
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus


def breakdown_quib(quib: Quib) -> Set[Quib]:
    quib_type = quib.get_type()
    if issubclass(quib_type, np.ndarray):
        return {quib[idx] for idx in np.ndindex(quib.get_shape().get_value())}
    if issubclass(quib_type, (np.generic, int)):
        return set()
    if issubclass(quib_type, (tuple, list)):
        return reduce(or_, (breakdown_quib(sub_quib) for sub_quib in quib.iter_first(len(quib.get_value()))))
    raise TypeError(f'Unsupported quib type: {quib_type}')


def check_invalidation(func, data, indices_to_invalidate):
    """
    Run func on an ndarray iquib, change the iquib in the given indices,
    and verify that the invalidated children were also the ones that changed values.
    Make sure that func works in a way that guarantees that when a value in the input changes,
    all affected values in the result also change.
    """
    input_quib = iquib(data)
    result = func(input_quib)
    result.set_cache_behavior(CacheBehavior.OFF)
    children = breakdown_quib(result)

    original_values = {child: child.get_value() for child in children}
    input_quib[indices_to_invalidate] = 999

    invalidated_children = {child for child in children if child.cache_status == CacheStatus.ALL_INVALID}
    changed_children = {child for child in children if child.get_value() != original_values[child]}
    assert invalidated_children == changed_children
