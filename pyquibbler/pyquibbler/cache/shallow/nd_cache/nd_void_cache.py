from typing import Any, List

import numpy as np

from pyquibbler.path import PathComponent
from pyquibbler.cache.shallow.nd_cache.nd_indexable_cache import NdIndexableCache


class NdVoidCache(NdIndexableCache):
    """
    Represents an np.void object that was
    """
    SUPPORTING_TYPES = (np.void,)

    def __init__(self, value: Any, mask):
        super(NdVoidCache, self).__init__(value, mask)

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=[(name, np.bool_) for name in result.dtype.names])
        mask = np.void(mask)
        return cls(result, mask=mask)

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        # np.void's are interesting- although they can be indexed, they are still zero dimensional, and therefore
        # certain indexing methods work and certain don't:
        # You can reference np.void by `True`, `...`, or indexes (but not slices)

        if path_component.component is True or path_component.component is ...:
            return [
                [PathComponent(name)] for name in self._invalid_mask.dtype.names if self._invalid_mask[name]
            ]

        if bool(self._invalid_mask[path_component.component]) is True:
            return [[path_component]]

        return []

    def _is_completely_invalid(self):
        return all(np.all(self._invalid_mask[name]) for name in self._invalid_mask.dtype.names)
