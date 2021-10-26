from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from functools import wraps
from typing import Any, List, Optional, Tuple, Type

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.cache import Cache, CacheStatus
from pyquibbler.quib.utils import deep_copy_without_quibs_or_artists


class PathCannotHaveComponentsException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


class ShallowCache(Cache):
    """
    A base class for any "shallow" caches- a shallow cache is a cache which only supports validation and invalidation
    one component in.
    This base class only supports entire validations/invalidations without any specificity, but provides the functions
    to override in order to support this
    """

    SUPPORTING_TYPES = (object,)

    def __init__(self, value: Any, object_is_invalidated_as_a_whole: bool):
        super().__init__(value)
        self._object_is_invalidated_as_a_whole = object_is_invalidated_as_a_whole

    @classmethod
    def create_from_result(cls, result):
        return cls(result, True)

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
        """
        Override this function in a subclass given an implementation to set valid at specific components
        """
        raise PathCannotHaveComponentsException()

    def _set_valid_value_all_paths(self, value):
        """
        Set the cache to be completely valid.
        Override this in order to update anything other you have which represents validity (such as a mask)
        """
        self._value = value

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) != 0:
            self._set_invalid_at_path_component(path[0])
        else:
            self._object_is_invalidated_as_a_whole = True

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        """
        Override this function in a subclass given an implementation to invalidate at specific components
        """
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
        """
        Get all uncached paths that derive from a given path component (this must be a subset of the path component
        or the path component itself)
        """
        return [[path_component]] if self._object_is_invalidated_as_a_whole else []

    def _is_completely_invalid(self):
        """
        Is this cache completely invalid?
        Override this in order to add an implementation for partial invalidation that led to complete invalidation
        """
        return self._object_is_invalidated_as_a_whole
