from typing import Any, List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache, CacheStatus


class NdShallowCache(ShallowCache):
    # TODO: Maybe change name to match module?

    SUPPORTING_TYPES = (np.ndarray,)

    def __init__(self, value: Any, whole_object_is_invalidated, mask):
        super(NdShallowCache, self).__init__(value, whole_object_is_invalidated)
        self._invalid_mask = mask
        self._whole_object_is_invalidated = whole_object_is_invalidated

    def matches_result(self, result):
        return super(NdShallowCache, self).matches_result(result) \
               and result.shape == self.get_value().shape and result.dtype == self.get_value().dtype

    def _is_completely_invalid(self):
        if self._invalid_mask.dtype.names:
            invalid = all(np.all(self._invalid_mask[name]) for name in self._invalid_mask.dtype.names)
        else:
            invalid = np.all(self._invalid_mask)
        return super(NdShallowCache, self)._is_completely_invalid() or invalid

    @classmethod
    def create_from_result(cls, result):
        dtype = np.bool_
        if result.dtype.names is not None:
            dtype = [(name, np.bool_) for name in result.dtype.names]
        mask = np.full(result.shape, True, dtype=dtype)
        return cls(result, True, mask)

    def _set_valid_value_all_paths(self, value):
        super(NdShallowCache, self)._set_valid_value_all_paths(value)

        dtype = np.bool_
        if value.dtype.names is not None:
            dtype = [(name, np.bool_) for name in value.dtype.names]
        mask = np.full(value.shape, False, dtype=dtype)

        self._invalid_mask = mask

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        if self._invalid_mask.dtype.names is None:
            self._invalid_mask[path_component.component] = True
        elif self._invalid_mask.dtype is not None and not path_component.references_field_in_field_array():
            for name in self._invalid_mask.dtype.names:
                self._invalid_mask[name] = True

    def _get_uncached_paths_at_indices(self, indices):
        paths = []
        boolean_mask_of_indices = create_empty_array_with_values_at_indices(
            self._value.shape,
            indices=indices,
            value=True,
            empty_value=False
        )

        if self._value.dtype.names:
            for name in self._value.dtype.names:
                paths.append([PathComponent(indexed_cls=np.ndarray, component=name),
                              PathComponent(indexed_cls=np.ndarray, component=np.logical_and(
                                  boolean_mask_of_indices,
                                  self._invalid_mask[name]
                              ))])
        else:
            paths.append(
                [
                    PathComponent(indexed_cls=np.ndarray,
                                  component=np.logical_and(boolean_mask_of_indices, self._invalid_mask))
                ]
            )

        # TODO: do we really want this filter?
        return list(filter(lambda p: np.any(p[-1].component), paths))

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return super(NdShallowCache, self)._get_all_uncached_paths() or self._get_uncached_paths_at_indices(True)

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        paths = super(NdShallowCache, self)._get_uncached_paths_at_path_component(path_component)
        if paths:
            return paths

        if path_component.references_field_in_field_array():
            if np.any(self._invalid_mask[path_component.component]):
                return [[PathComponent(indexed_cls=np.ndarray, component=path_component.component),
                        PathComponent(indexed_cls=np.ndarray, component=self._invalid_mask[path_component.component])]]
            return []
        else:
            return self._get_uncached_paths_at_indices(path_component.component)

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value: Any):
        self._value[path_component.component] = value
        self._invalid_mask[path_component.component] = False
