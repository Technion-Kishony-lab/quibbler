from abc import abstractmethod
from typing import Any, List


from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.cache.cache import Cache
from pyquibbler.path import PathComponent, Path


class CannotInvalidateEntireCacheException(PyQuibblerException):

    def __str__(self):
        return "It is not possible to invalidate an entire shallow cache- as we are shallow, our size may have " \
               "changed given a complete invalidation"


class ShallowCache(Cache):
    """
    A base class for any "shallow" caches- a shallow cache is a cache which only supports validation and invalidation
    one component in.
    """

    SUPPORTING_TYPES = (object,)

    def __init__(self, value, invalid_mask):
        super(ShallowCache, self).__init__(value)
        self._invalid_mask = invalid_mask

    @abstractmethod
    def _set_valid_at_all_paths(self):
        """
        Set yourself to valid at all paths (the value will be switched)
        """
        pass

    @abstractmethod
    def _set_valid_value_at_path_component(self, path_component: PathComponent, value: Any):
        """
        Set a path to a valid value at a specific component
        """
        pass

    @abstractmethod
    def _set_invalid_at_path_component(self, path_component: PathComponent):
        """
        Invalidate at a specific path
        """
        pass

    @abstractmethod
    def _get_all_uncached_paths(self) -> List[Path]:
        """
        Get all uncached (invalid) paths which exist
        """
        pass

    @abstractmethod
    def _get_uncached_paths_at_path_component(self,
                                              path_component: PathComponent) \
            -> List[Path]:
        """
        Get all uncached paths that derive from a given path component (this must be a subset of the path component
        or the path component itself)
        """
        pass

    def set_valid_value_at_path(self, path: Path, value: Any) -> None:
        if len(path) != 0:
            self._set_valid_value_at_path_component(path[0], value)
        else:
            self._set_valid_at_all_paths()
            self._value = value

    def set_invalid_at_path(self, path: Path) -> None:
        if len(path) == 0:
            raise CannotInvalidateEntireCacheException()

        self._set_invalid_at_path_component(path[0])

    def get_uncached_paths(self, path: Path):
        if len(path) == 0:
            return self._get_all_uncached_paths()
        return self._get_uncached_paths_at_path_component(path[0])

    @abstractmethod
    def _is_completely_invalid(self):
        pass
