import numpy as np
from functools import wraps

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.cache.cache import Cache
from pyquibbler.path import Path, Paths, deep_get


class PathCannotHaveComponentsException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


def skip_if_path_is_false_or_raise_if_path_is_not_all(func):
    @wraps(func)
    def _wrapper(self, path: Path, *args, **kwargs):
        if len(path) > 0:
            fake_value = np.int64(3)
            try:
                get_fake_value = deep_get(fake_value, path)
            except Exception:
                raise PathCannotHaveComponentsException()
            if np.size(get_fake_value) == 0:
                # the path references 'nothing'
                return
            if np.size(get_fake_value) != 1 or not np.all(get_fake_value == fake_value):
                raise PathCannotHaveComponentsException()
        return func(self, [], *args, **kwargs)

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

    @skip_if_path_is_false_or_raise_if_path_is_not_all
    def set_valid_value_at_path(self, path: Path, value) -> None:
        self._invalid = False
        self._value = value

    @skip_if_path_is_false_or_raise_if_path_is_not_all
    def set_invalid_at_path(self, path: Path) -> None:
        self._invalid = True

    def get_uncached_paths(self, path: Path) -> Paths:
        return [[]] if self._invalid else []

    def _is_completely_invalid(self):
        return self._invalid
