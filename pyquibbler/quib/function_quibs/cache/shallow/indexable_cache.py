from typing import List, Any, Union, Type

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache


def transform_cache_to_nd_if_necessary_given_path(cache, path: List[PathComponent]):
    """
    If a path is attempting to access a cache as though it were an ndarray, we can attempt to transform into an ndarray
    so that it will be accessable as such.

    We mainly do this because a quib which represents a list may be transformed into an ndarray down the road
    (by putting it through any np function for example), and thereafter changed. If so, any paths created will be to an
    ndarray, and reverse assignment as well as invalidation will fail on the original list cache
    """
    from pyquibbler.quib.function_quibs.cache import create_cache
    if (len(path) > 0
            and path[0].indexed_cls == np.ndarray
            and isinstance(cache, IndexableCache)):
        uncached_paths = cache.get_uncached_paths([])
        cache = create_cache(np.array(cache.get_value()))
        for path in uncached_paths:
            cache.set_invalid_at_path(path)
    return cache


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

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        mask = [(i, obj) for i, obj in enumerate(self._value)]
        data = mask[path_component.component]

        if not isinstance(data, list):
            # We need to take care of slices
            data = [data]

        return [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in data
            if self._invalid_mask[i] is True
        ]

    def _set_invalid_mask_at_path_component(self, component: Union[int, slice], value: bool):
        if isinstance(component, slice):
            range_to_set_invalid = (component.start or 0, component.stop or len(self._value), component.step or 1)
        else:
            range_to_set_invalid = (component, component + 1)

        for i in range(*range_to_set_invalid):
            self._invalid_mask[i] = value

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value):
        self._value[path_component.component] = value
        self._set_invalid_mask_at_path_component(path_component.component, False)

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        self._set_invalid_mask_at_path_component(path_component.component, True)

    def _is_completely_invalid(self):
        return all(self._invalid_mask)

    def _set_valid_at_all_paths(self):
        self._invalid_mask = [False for _ in self._value]

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in enumerate(self._value)
            if self._invalid_mask[i] is True
        ]

    def get_value(self) -> Any:
        return self._original_type(super(IndexableCache, self).get_value())
