from typing import Any

import numpy as np

from pyquibbler.quib.function_quibs.cache.shallow.dict_cache import DictCache
from pyquibbler.quib.function_quibs.cache.shallow.list_cache import ListCache
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdFieldArrayShallowCache, NdUnstructuredArrayCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache


def create_cache(result: Any) -> ShallowCache:
    # TODO; make indexable cache (we have dupcode)

    cache_classes = {
        NdFieldArrayShallowCache,
        NdUnstructuredArrayCache,
        ListCache,
        DictCache
    }
    for cache_class in cache_classes:
        if cache_class.supports_result(result):
            return cache_class.create_from_result(result)
    return ShallowCache.create_from_result(result)