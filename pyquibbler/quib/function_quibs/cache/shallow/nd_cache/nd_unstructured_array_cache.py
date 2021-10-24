from typing import List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_array_cache import NdArrayCache
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices


class NdUnstructuredArrayCache(NdArrayCache):
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
        return cls(result, True, mask)

    def _is_completely_invalid(self):
        return super(NdUnstructuredArrayCache, self)._is_completely_invalid() or np.all(self._invalid_mask)

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        paths = super(NdUnstructuredArrayCache, self)._get_uncached_paths_at_path_component(path_component)
        if paths:
            return paths

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
