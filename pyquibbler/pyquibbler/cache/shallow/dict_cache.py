from typing import List

from pyquibbler.path import PathComponent
from pyquibbler.cache.shallow.shallow_cache import ShallowCache


class DictCache(ShallowCache):
    """
    A cache for a dictionary at a shallow level (by keys)
    """

    SUPPORTING_TYPES = (dict,)

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        return cls(result, invalid_mask={
                k: True
                for k in result
            })

    def matches_result(self, result):
        return super(DictCache, self).matches_result(result) \
               and list(result.keys()) == list(self._value.keys())

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) -> List[List[PathComponent]]:
        return [
            [PathComponent(k)]
            for k, v in self._value.items()
            if self._invalid_mask[k] is True
            and k == path_component.component
        ]

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return [
            [PathComponent(k)]
            for k, v in self._value.items()
            if self._invalid_mask[k] is True
        ]

    def _set_valid_at_all_paths(self):
        self._invalid_mask = {k: False for k in self._value}

    def _is_completely_invalid(self):
        return all(v is True for v in self._invalid_mask.values())
