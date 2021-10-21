from typing import List, Any

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache, invalid, CacheStatus


class ListShallowCache(ShallowCache):

    SUPPORTING_TYPES = (list,)

    @classmethod
    def create_from_result(cls, result):
        return cls([invalid for _ in result], True)

    def matches_result(self, result):
        return super(ListShallowCache, self).matches_result(result) \
               and len(result) == len(self.get_value())

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        mask = [(i, obj) for i, obj in enumerate(self._value)]
        data = mask[path_component.component]

        if not isinstance(data, list):
            # We need to take care of slices
            data = [data]

        return super(ListShallowCache, self)._get_uncached_paths_at_path_component(path_component) or [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in data
            if value is invalid
        ]

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return super(ListShallowCache, self)._get_all_uncached_paths() or [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in enumerate(self._value)
            if value is invalid
        ]

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value):
        self._value[path_component.component] = value

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        component = path_component.component
        if isinstance(component, slice):
            range_to_set_invalid = (component.start or 0, component.stop or len(self._value), component.step or 1)
        else:
            range_to_set_invalid = (component, component + 1)

        for i in range(*range_to_set_invalid):
            self._value[i] = invalid
    
    def _is_completely_invalid(self):
        return super(ListShallowCache, self)._is_completely_invalid() or all(x is invalid for x in self._value)
    