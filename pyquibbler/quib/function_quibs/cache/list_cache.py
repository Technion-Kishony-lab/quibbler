from typing import List, Any

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache, invalid


class ListShallowCache(ShallowCache):

    SUPPORTING_TYPES = (list,)

    @classmethod
    def create_from_result(cls, result):
        return cls([invalid for _ in result])

    def matches_result(self, result):
        return super(ListShallowCache, self).matches_result(result) \
               and len(result) == len(self.get_value())

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) == 0:
            range_to_set_invalid = (len(self._value),)
        else:
            component = path[0].component
            if isinstance(component, slice):
                range_to_set_invalid = (component.start or 0, component.stop or len(self._value), component.step or 1)
            else:
                range_to_set_invalid = (component, component + 1)

        for i in range(*range_to_set_invalid):
            self._value[i] = invalid

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        self._value = deep_assign_data_with_paths(self._value, path, value)

    def get_uncached_paths(self, path):
        mask = [(i, obj) for i, obj in enumerate(self._value)]
        data = get_sub_data_from_object_in_path(mask, path)
        if not isinstance(data, list):
            data = [data]

        return [
            [PathComponent(indexed_cls=list, component=i)]
            for i, value in data
            if value is invalid
        ]
