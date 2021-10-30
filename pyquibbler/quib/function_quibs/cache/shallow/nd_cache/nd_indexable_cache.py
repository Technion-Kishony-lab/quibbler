from typing import Any, List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache


class NdIndexableCache(ShallowCache):
    """
    A base class for an ndarray cache (both unstructured and field array)
    """

    SUPPORTING_TYPES = (np.ndarray,)

    def __init__(self, value: Any, mask):
        super(NdIndexableCache, self).__init__(value)
        self._invalid_mask = mask

    def matches_result(self, result) -> bool:
        return super(NdIndexableCache, self).matches_result(result) \
               and result.shape == self.get_value().shape and result.dtype == self.get_value().dtype

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        self._invalid_mask[path_component.component] = True

    def _set_valid_value_all_paths(self, value):
        super(NdIndexableCache, self)._set_valid_value_all_paths(value)
        mask = np.full(value.shape, False, dtype=self._invalid_mask.dtype)
        if isinstance(self._invalid_mask, np.void):
            self._invalid_mask = np.void(mask)
        else:
            self._invalid_mask = mask

    def _set_valid_at_path_component(self, path_component: PathComponent):
        self._invalid_mask[path_component.component] = False

    def _set_value_at_path_component(self, path_component: PathComponent, value: Any):
        self._value[path_component.component] = value

    @staticmethod
    def _filter_empty_paths(paths):
        return list(filter(lambda p: np.any(p[-1].component), paths))

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return self._get_uncached_paths_at_path_component(PathComponent(component=True, indexed_cls=type(self._value)))
