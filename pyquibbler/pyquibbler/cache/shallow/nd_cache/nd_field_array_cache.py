import numpy as np

from pyquibbler.cache.shallow.nd_cache.nd_indexable_cache import NdIndexableCache
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices
from pyquibbler.path import PathComponent


class NdFieldArrayShallowCache(NdIndexableCache):
    """
    A cache for any ndarray which has dtype names (ie a "field array")
    """

    SUPPORTING_TYPES = (np.ndarray,)

    @classmethod
    def supports_result(cls, result):
        return super(NdFieldArrayShallowCache, cls).supports_result(result) and result.dtype.names is not None

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=[(name, np.bool_) for name in result.dtype.names])
        return cls(
            result,
            invalid_mask=mask
        )

    def _create_paths_for_indices(self, indices):
        boolean_mask_of_indices = create_bool_mask_with_true_at_indices(self._value.shape, indices)

        return [
            [PathComponent(name),
             PathComponent(np.logical_and(
                 boolean_mask_of_indices,
                 self._invalid_mask[name]
             ))]
            for name in self._invalid_mask.dtype.names
        ]

    def _get_uncached_paths_at_path_component(self,
                                              path_component):
        if path_component.referencing_field_in_field_array(type(self._value)):
            paths = [[PathComponent(path_component.component),
                      PathComponent(np.array(self._invalid_mask[path_component.component]))]]
        else:
            paths = self._create_paths_for_indices(path_component.component)

        return self._filter_empty_paths(paths)

    def _is_completely_invalid(self):
        return all(np.all(self._invalid_mask[name]) for name in self._invalid_mask.dtype.names)
