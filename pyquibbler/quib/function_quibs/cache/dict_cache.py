from typing import List, Any

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache, invalid


class DictShallowCache(ShallowCache):

    def matches_result(self, result):
        return super(DictShallowCache, self).matches_result(result) \
               and list(result.keys()) == list(self._value.keys())

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) == 0:
            self._value = {k: invalid for k, _ in self._value.items()}
        else:
            self._value = deep_assign_data_with_paths(self._value, path, invalid)

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        self._value = deep_assign_data_with_paths(self._value, path, value)

    def get_uncached_paths(self, path):
        data = get_sub_data_from_object_in_path(self._value, path)
        return [path] if data is invalid else []
