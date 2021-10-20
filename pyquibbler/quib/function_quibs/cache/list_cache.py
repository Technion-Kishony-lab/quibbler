from typing import List, Any

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache, invalid


class ListShallowCache(ShallowCache):

    def matches_result(self, result):
        return super(ListShallowCache, self).matches_result(result) \
               and len(result) == len(self.get_value())

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) == 0:
            self._value = [invalid for _ in self._value]
        else:
            self._value = deep_assign_data_with_paths(self._value, path, invalid)

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
