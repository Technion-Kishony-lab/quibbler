from typing import List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_indexable_cache import NdIndexableCache
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices


class NdUnstructuredArrayCache(NdIndexableCache):
    """
    A cache for an ndarray which is NOT structured (rec/field)
    """

    SUPPORTING_TYPES = (np.ndarray,)

    @classmethod
    def supports_result(cls, result):
        return super(NdUnstructuredArrayCache, cls).supports_result(result) and result.dtype.names is None

    @classmethod
    def create_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=np.bool_)
        return cls(result, mask)

    def _is_completely_invalid(self):
        return np.all(self._invalid_mask)

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        boolean_mask_of_indices = create_empty_array_with_values_at_indices(
            self._value.shape,
            indices=path_component.component,
            value=True,
            empty_value=False
        )

        return self._filter_empty_paths([
                    [PathComponent(indexed_cls=np.ndarray,
                                   component=np.logical_and(boolean_mask_of_indices, self._invalid_mask))]
                ])
