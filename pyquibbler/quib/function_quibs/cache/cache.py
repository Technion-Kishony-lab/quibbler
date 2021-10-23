from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Type, List, Any

from pyquibbler.quib.assignment import PathComponent


class CacheStatus(Enum):
    ALL_INVALID = 0
    ALL_VALID = 1
    PARTIAL = 2


class Cache(ABC):

    SUPPORTING_TYPES: Tuple[Type] = NotImplemented

    def __init__(self, value):
        self._value = value

    @classmethod
    def create_from_result(cls, result):
        raise NotImplementedError()

    @classmethod
    def supports_result(cls, result):
        return isinstance(result, cls.SUPPORTING_TYPES)

    def matches_result(self, result) -> bool:
        return self.supports_result(result)

    @abstractmethod
    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        pass

    @abstractmethod
    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        pass

    @abstractmethod
    def get_uncached_paths(self, path: List[PathComponent]) -> List[List[PathComponent]]:
        pass

    @abstractmethod
    def get_cache_status(self) -> CacheStatus:
        pass

    def get_value(self) -> Any:
        return self._value
