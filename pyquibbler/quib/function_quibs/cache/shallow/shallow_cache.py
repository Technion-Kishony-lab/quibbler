from abc import abstractmethod
from typing import Any, List


from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.cache import Cache, CacheStatus


class InvalidationNotSupportedInNonPartialCacheException(PyQuibblerException):

    def __str__(self):
        return "You cannot invalidate a non partial cache (eg a whole number)"


class CannotInvalidateEntireCacheException(PyQuibblerException):

    def __str__(self):
        return "It is not possible to invalidate an entire shallow cache- as we are shallow, our size may have " \
               "changed given a complete invalidation"


class NonPartialShallowCacheCannotBeInvalidException(PyQuibblerException):

    def __str__(self):
        return "A shallow cache which is not partial cannot ever be invalid"


class ShallowCache(Cache):
    """
    A base class for any "shallow" caches- a shallow cache is a cache which only supports validation and invalidation
    one component in.
    This base class only supports entire validations/invalidations without any specificity, but provides the functions
    to override in order to support this
    """

    SUPPORTING_TYPES = (object,)

    @abstractmethod
    def _set_valid_at_all_paths(self):
        pass

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        if len(path) != 0:
            self._set_valid_value_at_path_component(path[0], value)
        else:
            self._set_valid_at_all_paths()
            self._value = value

    @abstractmethod
    def _set_valid_value_at_path_component(self, path_component: PathComponent, value: Any):
        """
        Override this function in a subclass given an implementation to set valid at specific components
        """
        pass

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) == 0:
            raise CannotInvalidateEntireCacheException()

        self._set_invalid_at_path_component(path[0])

    @abstractmethod
    def _set_invalid_at_path_component(self, path_component: PathComponent):
        """
        Override this function in a subclass given an implementation to invalidate at specific components
        """
        pass

    @abstractmethod
    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        pass

    def get_uncached_paths(self, path: List[PathComponent]):
        if len(path) == 0:
            return self._get_all_uncached_paths()
        return self._get_uncached_paths_at_path_component(path[0])

    @abstractmethod
    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent)\
            -> List[List[PathComponent]]:
        """
        Get all uncached paths that derive from a given path component (this must be a subset of the path component
        or the path component itself)

        As a shallowcache with no partial support, we are never invalidated
        """
        return []

    @abstractmethod
    def _is_completely_invalid(self):
        """
        Is this cache completely invalid?
        """
