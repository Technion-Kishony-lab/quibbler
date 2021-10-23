from typing import List, Any

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache, invalid


class DictCache(ShallowCache):

    SUPPORTING_TYPES = (dict,)

    @classmethod
    def create_from_result(cls, result):
        return cls(
            {
                k: invalid for k in result
            },
            True
        )

    def matches_result(self, result):
        return super(DictCache, self).matches_result(result) \
               and list(result.keys()) == list(self._value.keys())

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value: Any):
        self._value[path_component.component] = value

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        self._value[path_component.component] = invalid

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        return super(DictCache, self)._get_uncached_paths_at_path_component(path_component) or [
            [PathComponent(component=k, indexed_cls=dict)]
            for k, v in self._value.items()
            if v is invalid
            and k == path_component.component
        ]

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return super(DictCache, self)._get_all_uncached_paths() or [
            [PathComponent(component=k, indexed_cls=dict)]
            for k, v in self._value.items()
            if v is invalid
        ]