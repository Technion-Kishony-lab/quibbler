from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Type, List, Any

from pyquibbler.quib.assignment import PathComponent


class CacheStatus(Enum):
    ALL_INVALID = 0
    ALL_VALID = 1
    PARTIAL = 2


class Cache(ABC):
    """
    A cache is an object which supports storing and invalidating values at specific paths.
    """

    SUPPORTING_TYPES: Tuple[Type] = NotImplemented

    def __init__(self, value):
        self._value = value

    def __repr__(self):
        return f"<{self.__class__.__name__} - (type: {self._value.__class__.__name__})>"

    @classmethod
    def supports_result(cls, result):
        """
        Does this cache class support the given result?
        """
        return isinstance(result, cls.SUPPORTING_TYPES)

    @classmethod
    def create_invalid_cache_from_result(cls, result):
        """
        Create a completely invalid cache from a result- this result is considered interesting in shape only,
        and any cache should begin entirely invalidated when called from this function
        """
        raise NotImplementedError()

    def matches_result(self, result) -> bool:
        """
        Does this cache *instance* support this given result?
        Note that it is possible for a cache class to support a given result, while the specific instance does not
        """
        return self.supports_result(result)

    @abstractmethod
    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        """
        Store a valid value at a given path within the cache
        """

    @abstractmethod
    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        """
        Set any values found at these paths to invalid
        """

    @abstractmethod
    def get_uncached_paths(self, path: List[PathComponent]) -> List[List[PathComponent]]:
        """
        Get a list of paths which do not have cached values and interstect with the argument path.
        For example, if `path` were to be an empty list `[]` (meaning "everything"), then all uncached paths would be
        returned (anything invalid)
        """

    def get_cache_status(self) -> CacheStatus:
        """
        Get the current status of the cache, options of which are marked by the enum `CacheStatus`
        """
        uncached_paths = self.get_uncached_paths([])
        if len(uncached_paths) == 0:
            return CacheStatus.ALL_VALID
        elif self.is_completely_invalid_at_path([]):
            return CacheStatus.ALL_INVALID
        else:
            return CacheStatus.PARTIAL

    def is_completely_invalid_at_path(self, path: List[PathComponent]):
        """
        Is this cache completely invalid?
        """
        get_sub

    def get_value(self) -> Any:
        """
        Get the current value; this value may not be completely valid, but it is promised to be in the same "shape"
        (not specifically an np reference here) as the real value.
        """
        return self._value
