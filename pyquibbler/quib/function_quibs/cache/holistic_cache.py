from functools import wraps
from typing import List

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.cache import Cache


class PathCannotHaveComponentsException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


def raise_if_path_is_not_empty(func):
    @wraps(func)
    def _wrapper(self, path, *args, **kwargs):
        if len(path) > 0:
            raise PathCannotHaveComponentsException()
        return func(self, path, *args, **kwargs)
    return _wrapper


class HolisticCache(Cache):
    """
    A holistic cache cannot be referenced by a field or item within it- it's an all or nothing cache. This is ideal
    for things which cannot be broken up into parts, like numbers (as opposed to lists)
    """

    SUPPORTING_TYPES = (object,)

    def __init__(self, value, invalid):
        super(HolisticCache, self).__init__(value)
        self._invalid = invalid

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        return cls(value=result, invalid=True)

    @raise_if_path_is_not_empty
    def set_valid_value_at_path(self, path: List[PathComponent], value) -> None:
        self._invalid = False
        self._value = value

    @raise_if_path_is_not_empty
    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        self._invalid = True

    def get_uncached_paths(self, path: List[PathComponent]) -> List[List[PathComponent]]:
        return [path] if self._invalid else []

    def _is_completely_invalid(self):
        return self._invalid

    @raise_if_path_is_not_empty
    def is_completely_invalid_at_path(self, path: List[PathComponent]):
        return self._invalid

