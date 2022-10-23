from typing import List, Any, Type

import numpy as np

from pyquibbler.path import PathComponent, Paths, Path
from pyquibbler.cache.shallow.shallow_cache import ShallowCache
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices


class IndexableCache(ShallowCache):
    """
    Represents a cache that can be indexed (integer-indexed), for example lists and tuples
    """

    SUPPORTING_TYPES = (list, tuple,)

    def __init__(self, value: Any, original_type: Type, invalid_mask: List):
        super().__init__(value, invalid_mask)
        self._original_type = original_type

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        return cls(list(result), original_type=type(result), invalid_mask=[True for _ in result])

    def matches_result(self, result):
        return super(IndexableCache, self).matches_result(result) \
               and len(result) == len(self.get_value()) \
               and self._original_type == type(result)

    def _get_uncached_paths_at_path_component(self, path_component: PathComponent) -> Paths:
        if isinstance(self._value, np.ndarray) or path_component.is_nd_reference():
            boolean_mask_of_indices = create_bool_mask_with_true_at_indices(self._shape(), path_component.component)

            return self._filter_empty_paths([
                [PathComponent(np.logical_and(boolean_mask_of_indices, self._invalid_mask_broadcasted()))]
            ])

        mask = [(i, obj) for i, obj in enumerate(self._value)]
        data = mask[path_component.component]

        if not isinstance(data, list):
            # We need to take care of slices
            data = [data]

        return [
            [PathComponent(i)]
            for i, value in data
            if self._invalid_mask[i] is True
        ]

    def _set_invalid_mask_at_non_empty_path(self, path: Path, value: bool) -> None:
        path_component = path[0]
        component = path_component.component
        if isinstance(self._value, np.ndarray) or path_component.is_nd_reference():
            nd_invalid_mask = self._invalid_mask_broadcasted()
            nd_invalid_mask[component] = value
            self._invalid_mask = self._unbroadcast_invalid_mask(nd_invalid_mask)
            return

        if isinstance(component, slice):
            range_to_set_invalid = (component.start or 0, component.stop or len(self._value), component.step or 1)
        else:
            range_to_set_invalid = (component, component + 1)

        for i in range(*range_to_set_invalid):
            if i < len(self._invalid_mask):
                self._invalid_mask[i] = value
            # If the user attempts to set valid out of bounds, we don't need to do anything-
            # this can arise if:
            # `a = iquib([1, 2, 3]); b = a[4:5]; b.get_value();
            # as python allows accessing slices out of bounds

    def _is_completely_invalid(self):
        return all(self._invalid_mask)

    def _set_valid_at_all_paths(self):
        self._invalid_mask = [False for _ in self._value]

    def _get_all_uncached_paths(self) -> Paths:
        return [
            [PathComponent(i)] for i, _ in enumerate(self._value) if self._invalid_mask[i]
        ]

    def _shape(self):
        return np.shape(self._value)

    def _invalid_mask_broadcasted(self):
        # e.g, value=[[1,2],[3,4],[5,6]]; invalid_mask=[1,0,1] -> [[1,1],[0,0],[1,1]]
        return np.tile(self._invalid_mask, self._shape()[-1:0:-1] + (1,)).T

    def get_value(self) -> Any:
        return self._original_type(super(IndexableCache, self).get_value())

    @staticmethod
    def _unbroadcast_invalid_mask(mask: np.ndarray) -> list:
        return list(np.any(mask, tuple(range(1, mask.ndim))))

    @staticmethod
    def _filter_empty_paths(paths):
        return list(filter(lambda p: np.any(p[-1].component), paths))
