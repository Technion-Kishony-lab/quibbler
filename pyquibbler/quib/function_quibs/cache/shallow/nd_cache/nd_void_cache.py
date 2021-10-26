from typing import Any, List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_array_cache import NdArrayCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache


class NdVoidCache(NdArrayCache):
    SUPPORTING_TYPES = (np.void,)

    def __init__(self, value: Any, whole_object_is_invalidated, mask):
        super(NdVoidCache, self).__init__(value, whole_object_is_invalidated, mask)

    @classmethod
    def create_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=[(name, np.bool_) for name in result.dtype.names])
        mask = np.void(mask)
        return cls(result, True, mask)

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        paths = super(NdVoidCache, self)._get_uncached_paths_at_path_component(path_component)
        if paths:
            return paths

        if path_component.component is True or path_component.component is ...:
            return [
                [PathComponent(indexed_cls=np.void, component=name)]
                for name in self._invalid_mask.dtype.names
                if self._invalid_mask[name]
            ]

        if bool(self._invalid_mask[path_component.component]) is True:
            return [[path_component]]

        return []

