from typing import Any, List, Type, Union

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import \
    ShallowCache


class IndexableCache(ShallowCache):
    """
    Represents a cache that can be indexed (integer-indexed), for example lists and tuples
    """

    SUPPORTING_TYPES = (list, tuple,)

    def __init__(self, value: Any, object_is_invalidated_as_a_whole: bool, invalid_mask: List, original_type: Type):
        super().__init__(value, object_is_invalidated_as_a_whole)
        self._invalid_mask = invalid_mask
        self._original_type = original_type

    @classmethod
    def create_from_result(cls, result):
        return cls(list(result), True, [True for _ in result], type(result))

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

        return super(IndexableCache, self)._get_uncached_paths_at_path_component(path_component) or [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in data
            if self._invalid_mask[i] is True
        ]

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return super(IndexableCache, self)._get_all_uncached_paths() or [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in enumerate(self._value)
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
        return super(IndexableCache, self)._is_completely_invalid() or all(self._invalid_mask)

    def _set_valid_value_all_paths(self, value):
        super(IndexableCache, self)._set_valid_value_all_paths(value)
        self._invalid_mask = [False for _ in value]

    def get_value(self) -> Any:
        return self._original_type(super(IndexableCache, self).get_value())
