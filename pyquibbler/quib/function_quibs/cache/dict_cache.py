from typing import List, Any

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow_cache import ShallowCache, invalid


class DictShallowCache(ShallowCache):

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
        return super(DictShallowCache, self).matches_result(result) \
               and list(result.keys()) == list(self._value.keys())

