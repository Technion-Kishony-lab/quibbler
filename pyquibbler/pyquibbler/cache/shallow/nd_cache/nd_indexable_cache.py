from abc import ABC
from typing import List

import numpy as np

from pyquibbler.path import PathComponent
from pyquibbler.cache.shallow.shallow_cache import ShallowCache


class NdIndexableCache(ShallowCache, ABC):
    """
    A base class for an ndarray cache (both unstructured and field array)
    """

    SUPPORTING_TYPES = (np.ndarray,)

    def matches_result(self, result) -> bool:
        return super(NdIndexableCache, self).matches_result(result) \
               and result.shape == self.get_value().shape and result.dtype == self.get_value().dtype

    def _set_valid_at_all_paths(self):
        mask = np.full(self._value.shape, False, dtype=self._invalid_mask.dtype)
        if isinstance(self._invalid_mask, np.void):
            self._invalid_mask = np.void(mask)
        else:
            self._invalid_mask = mask

    @staticmethod
    def _filter_empty_paths(paths):
        return list(filter(lambda p: np.any(p[-1].component), paths))

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return self._get_uncached_paths_at_path_component(PathComponent(True))

    def make_a_copy_if_value_is_a_view(self):
        if isinstance(self._value, np.ndarray) and self._value.base is not None:
            # array is a "view". We need to make a copy.
            self._value = np.array(self._value)
