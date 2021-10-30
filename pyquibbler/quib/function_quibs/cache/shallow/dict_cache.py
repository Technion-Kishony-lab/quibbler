from typing import List, Any, Dict

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import ShallowCache


class DictCache(ShallowCache):
    """
    A cache for a dictionary at a shallow level (by keys)
    """

    SUPPORTING_TYPES = (dict,)

    def __init__(self, value: Any, invalid_mask: Dict):
        super().__init__(value)
        self._invalid_mask = invalid_mask

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        return cls(result, invalid_mask={
                k: True
                for k in result
            })

    def matches_result(self, result):
        return super(DictCache, self).matches_result(result) \
               and list(result.keys()) == list(self._value.keys())

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value):
        self._invalid_mask[path_component.component] = False
        self._value[path_component.component] = value

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        self._invalid_mask[path_component.component] = True

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        return [
            [PathComponent(component=k, indexed_cls=dict)]
            for k, v in self._value.items()
            if self._invalid_mask[k] is True
            and k == path_component.component
        ]

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return [
            [PathComponent(component=k, indexed_cls=dict)]
            for k, v in self._value.items()
            if self._invalid_mask[k] is True
        ]

    def _set_valid_at_all_paths(self):
        self._invalid_mask = {k: False for k in self._value}

    def _is_completely_invalid(self):
        return all(v is True for v in self._invalid_mask.values())
