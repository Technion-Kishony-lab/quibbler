from typing import Any

from .holistic_cache import HolisticCache
from .shallow import NdVoidCache
from .shallow.dict_cache import DictCache
from .shallow.indexable_cache import IndexableCache
from .shallow.nd_cache import NdFieldArrayShallowCache, NdUnstructuredArrayCache
from .shallow.shallow_cache import ShallowCache
from .cache import Cache, CacheStatus
from .holistic_cache import PathCannotHaveComponentsException
from .cache_utils import get_uncached_paths_matching_path, \
    get_cached_data_at_truncated_path_given_result_at_uncached_path


def create_cache(result: Any) -> ShallowCache:
    """
    Create a new cache object matching the result- if no cache is found that specifically supports the requested
    object, a shallow cache will be created which does not support partial invalidation (paths must be whole in
    validation and invalidation)
    """

    cache_classes = {
        NdFieldArrayShallowCache,
        NdUnstructuredArrayCache,
        IndexableCache,
        NdVoidCache,
        DictCache
    }
    for cache_class in cache_classes:
        if cache_class.supports_result(result):
            return cache_class.create_invalid_cache_from_result(result)
    return HolisticCache.create_invalid_cache_from_result(result)
