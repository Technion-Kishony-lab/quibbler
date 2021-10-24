from abc import ABCMeta, abstractmethod
from typing import Any, List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache


class NdArrayCache(ShallowCache):
    """
    A base class for an ndarray cache (both unstructured and field array)
    """

    SUPPORTING_TYPES = (np.ndarray,)

    def __init__(self, value: Any, whole_object_is_invalidated, mask):
        super(NdArrayCache, self).__init__(value, whole_object_is_invalidated)
        self._invalid_mask = mask
        self._whole_object_is_invalidated = whole_object_is_invalidated

    def matches_result(self, result) -> bool:
        return super(NdArrayCache, self).matches_result(result) \
               and result.shape == self.get_value().shape and result.dtype == self.get_value().dtype

    @classmethod
    def create_from_result(cls, result):
        raise NotImplementedError()

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        self._invalid_mask[path_component.component] = True

    def _set_valid_value_all_paths(self, value):
        super(NdArrayCache, self)._set_valid_value_all_paths(value)
        mask = np.full(value.shape, False, dtype=self._invalid_mask.dtype)
        self._invalid_mask = mask

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value: Any):
        self._value[path_component.component] = value
        self._invalid_mask[path_component.component] = False

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return super(NdArrayCache, self)._get_all_uncached_paths() \
               or self._get_uncached_paths_at_path_component(PathComponent(component=True, indexed_cls=np.ndarray))

    @staticmethod
    def _filter_empty_paths(paths):
        return list(filter(lambda p: np.any(p[-1].component), paths))
