from typing import List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_array_cache import NdArrayCache


class NdUnstructuredArrayCache(NdArrayCache):
    # TODO: Maybe change name to match module?

    SUPPORTING_TYPES = (np.ndarray,)

    @classmethod
    def supports_result(cls, result):
        return super(NdUnstructuredArrayCache, cls).supports_result(result) and result.dtype.names is None

    def _is_completely_invalid(self):
        if self._invalid_mask.dtype.names:
            invalid = all(np.all(self._invalid_mask[name]) for name in self._invalid_mask.dtype.names)
        else:
            invalid = np.all(self._invalid_mask)
        return super(NdUnstructuredArrayCache, self)._is_completely_invalid() or invalid

    @classmethod
    def create_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=np.bool_)
        return cls(result, True, mask)

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        if self._invalid_mask.dtype.names is None:
            self._invalid_mask[path_component.component] = True
        elif not path_component.references_field_in_field_array():
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
        return super(NdUnstructuredArrayCache, self)._get_all_uncached_paths() or self._get_uncached_paths_at_indices(True)

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        paths = super(NdUnstructuredArrayCache, self)._get_uncached_paths_at_path_component(path_component)
        if paths:
            return paths

        if path_component.references_field_in_field_array():
            if np.any(self._invalid_mask[path_component.component]):
                return [[PathComponent(indexed_cls=np.ndarray, component=path_component.component),
                        PathComponent(indexed_cls=np.ndarray, component=self._invalid_mask[path_component.component])]]
            return []
        else:
            return self._get_uncached_paths_at_indices(path_component.component)
