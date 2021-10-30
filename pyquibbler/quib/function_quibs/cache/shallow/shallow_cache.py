from typing import Any, List


from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.cache import Cache, CacheStatus


class InvalidationNotSupportedInNonPartialCacheException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


class CannotInvalidateEntireCacheException(PyQuibblerException):

    def __str__(self):
        return "It is not possible to invalidate an entire cache"


class ShallowCache(Cache):
    """
    A base class for any "shallow" caches- a shallow cache is a cache which only supports validation and invalidation
    one component in.
    This base class only supports entire validations/invalidations without any specificity, but provides the functions
    to override in order to support this
    """

    SUPPORTING_TYPES = (object,)

    @classmethod
    def create_from_result(cls, result, valid_path, **kwargs):
        self = cls(result, **kwargs)
        if len(valid_path) > 0:
            self._set_valid_at_path_component(valid_path[0])
        return self

    def get_cache_status(self):
        uncached_paths = self.get_uncached_paths([])
        if len(uncached_paths) == 0:
            return CacheStatus.ALL_VALID
        elif self._is_completely_invalid():
            return CacheStatus.ALL_INVALID
        else:
            return CacheStatus.PARTIAL

    def _set_valid_at_path_component(self, path_component: PathComponent):
        pass

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        if len(path) != 0:
            self._set_valid_at_path_component(path[0])
            self._set_value_at_path_component(path[0], value)
        else:
            self._set_valid_value_all_paths(value)

    def _set_value_at_path_component(self, path_component: PathComponent, value: Any):
        """
        Override this function in a subclass given an implementation to set valid at specific components
        """
        raise InvalidationNotSupportedInNonPartialCacheException()

    def _set_valid_value_all_paths(self, value):
        """
        Set the cache to be completely valid.
        Override this in order to update anything other you have which represents validity (such as a mask)
        """
        self._value = value

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) == 0:
            raise CannotInvalidateEntireCacheException()

        self._set_invalid_at_path_component(path[0])

    def _set_invalid_at_path_component(self, path_component: PathComponent):
        """
        Override this function in a subclass given an implementation to invalidate at specific components
        """
        raise InvalidationNotSupportedInNonPartialCacheException()

    def _get_all_uncached_paths(self) -> List[List[PathComponent]]:
        return []

    def get_uncached_paths(self, path: List[PathComponent]):
        if len(path) == 0:
            return self._get_all_uncached_paths()
        return self._get_uncached_paths_at_path_component(path[0])

    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent)\
            -> List[List[PathComponent]]:
        """
        Get all uncached paths that derive from a given path component (this must be a subset of the path component
        or the path component itself)

        As a shallowcache with no partial support, we are never invalidated
        """
        return []

    def _is_completely_invalid(self):
        """
        Is this cache completely invalid?
        Override this in order to add an implementation for partial invalidation that led to complete invalidation
        """
        return False
