from typing import Any

import numpy as np

from pyquibbler.quib.function_quibs.cache.dict_cache import DictShallowCache
from pyquibbler.quib.function_quibs.cache.list_cache import ListShallowCache
from pyquibbler.quib.function_quibs.cache.nd_array_cache import NdShallowCache
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache


def create_cache(result: Any) -> ShallowCache:
    # TODO; make indexable cache (we have dupcode)

    # Todo: make work with SUPPORTING_TYPES
    types_to_caches = {
        np.ndarray: NdShallowCache,
        list: ListShallowCache,
        dict: DictShallowCache
    }
    for type_, cache_class in types_to_caches.items():
        if isinstance(result, type_):
            return cache_class.create_from_result(result)
    return ShallowCache.create_from_result(result)