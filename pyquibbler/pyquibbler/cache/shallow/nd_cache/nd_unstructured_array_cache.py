from typing import List

import numpy as np

from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices
from pyquibbler.path import PathComponent
from pyquibbler.cache.shallow.nd_cache.nd_indexable_cache import NdIndexableCache


class NdUnstructuredArrayCache(NdIndexableCache):
    """
    A cache for an ndarray which is NOT structured (rec/field)
    """

    SUPPORTING_TYPES = (np.ndarray,)

    @classmethod
    def supports_result(cls, result):
        return super(NdUnstructuredArrayCache, cls).supports_result(result) and result.dtype.names is None

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=np.bool_)
        return cls(result, invalid_mask=mask)

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return self._get_uncached_paths_at_path_component(PathComponent(True))

    def _is_completely_invalid(self):
        return np.all(self._invalid_mask)

    def _get_uncached_paths_at_path_component(self, path_component: PathComponent) -> List[List[PathComponent]]:
        boolean_mask_of_indices = create_bool_mask_with_true_at_indices(self._value.shape, path_component.component)

        return self._filter_empty_paths([
                    [PathComponent(np.logical_and(boolean_mask_of_indices, self._invalid_mask))]
                ])
