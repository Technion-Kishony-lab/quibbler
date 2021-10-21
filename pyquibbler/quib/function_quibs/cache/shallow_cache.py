from abc import ABC, abstractmethod, ABCMeta
from enum import Enum
from functools import wraps
from typing import List, Any, Optional, Type, Tuple

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.utils import deep_copy_without_quibs_or_artists


class Invalid:
    pass


invalid = Invalid()


class CacheStatus(Enum):
    ALL_INVALID = 0
    ALL_VALID = 1
    PARTIAL = 2


class PathCannotHaveComponentsException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


class Cache(ABC):

    SUPPORTING_TYPES: Tuple[Type] = NotImplemented

    def __init__(self, value):
        self._value = value

    @classmethod
    def create_from_result(cls, result):
        raise NotImplementedError()

    def matches_result(self, result) -> bool:
        return isinstance(result, self.SUPPORTING_TYPES)

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


class ShallowCache(Cache):

    SUPPORTING_TYPES = (object,)

    def __init__(self, value: Any, object_is_invalidated_as_a_whole: bool):
        super().__init__(value)
        self._object_is_invalidated_as_a_whole = object_is_invalidated_as_a_whole

    @classmethod
    def create_from_result(cls, result):
        # We always start completely invalid
        return cls(invalid, True)

    def get_cache_status(self):
        uncached_paths = self.get_uncached_paths([])
        if len(uncached_paths) == 0:
            return CacheStatus.ALL_VALID
        elif self._is_completely_invalid():
            return CacheStatus.ALL_INVALID
        else:
            return CacheStatus.PARTIAL

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        self._object_is_invalidated_as_a_whole = False
        if len(path) != 0:
            self._set_valid_value_at_path_component(path[0], value)
        else:
            self._set_valid_value_all_paths(value)

    def _set_valid_value_at_path_component(self, path_component: PathComponent, value: Any):
        raise PathCannotHaveComponentsException()

    def _set_valid_value_all_paths(self, value):
        self._value = value

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) != 0:
            self._set_invalid_at_path_component(path[0])
        else:
            self._object_is_invalidated_as_a_whole = True

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        raise PathCannotHaveComponentsException()

    def get_uncached_paths(self, path: List[PathComponent]):
        if len(path) == 0:
            return self._get_all_uncached_paths()
        else:
            return self._get_uncached_paths_at_path_component(path[0])

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return [[]] if self._object_is_invalidated_as_a_whole else []

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent)\
            -> List[List[PathComponent]]:
        return [[path_component]] if self._object_is_invalidated_as_a_whole else []

    def _is_completely_invalid(self):
        return self._object_is_invalidated_as_a_whole
