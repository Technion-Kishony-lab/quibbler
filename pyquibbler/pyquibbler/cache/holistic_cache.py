from functools import wraps

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.cache.cache import Cache
from pyquibbler.path import Path, Paths, SpecialComponent


class PathCannotHaveComponentsException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


def raise_if_path_is_not_all(func):
    @wraps(func)
    def _wrapper(self, path: Path, *args, **kwargs):
        if not(len(path) == 0
               or len(path) == 1 and path[0].component in [False, True, SpecialComponent.WHOLE, SpecialComponent.ALL]):
            raise PathCannotHaveComponentsException()

        if len(path) == 0 or path[0].component is not False:
            return func(self, path, *args, **kwargs)

    return _wrapper


class HolisticCache(Cache):
    """
    A holistic cache cannot be referenced by a field or item within it- it's an all or nothing cache. This is ideal
    for things which cannot be broken up into parts, like numbers (as opposed to lists, or arrays)
    """

    SUPPORTING_TYPES = (object,)

    def __init__(self, value, invalid):
        super(HolisticCache, self).__init__(value)
        self._invalid = invalid

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        return cls(value=result, invalid=True)

    @raise_if_path_is_not_all
    def set_valid_value_at_path(self, path: Path, value) -> None:
        self._invalid = False
        self._value = value

    @raise_if_path_is_not_all
    def set_invalid_at_path(self, path: Path) -> None:
        self._invalid = True

    def get_uncached_paths(self, path: Path) -> Paths:
        return [path] if self._invalid else []

    def _is_completely_invalid(self):
        return self._invalid
