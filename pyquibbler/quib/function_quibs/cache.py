from functools import wraps
from typing import List, Any, Optional, Type

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path


class Invalid:
    pass


invalid = Invalid()


def ensure_initialized(func):
    @wraps(func)
    def _ensure(self, *args, **kwargs):
        if self._value is None:
            raise Exception()
        return func(*args, **kwargs)
    return _ensure


class ShallowCache:
    def __init__(self, value: Any):
        self._value = value

    def matches_result(self, result):
        return isinstance(result, type(self._value))

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        self._value = deep_assign_data_with_paths(self._value, path, value)

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        self._value = deep_assign_data_with_paths(self._value, path, invalid)

    def get_uncached_path(self, path):
        val = get_sub_data_from_object_in_path(self._value, path)
        if val is invalid:
            return path

    def is_valid_at_path(self, path) -> bool:
        val = get_sub_data_from_object_in_path(self._value, path)
        return val is not invalid

    def get_value(self) -> Any:
        return self._value


class NdShallowCache(ShallowCache):

    def __init__(self, value: Any, mask):
        super(NdShallowCache, self).__init__(value)
        self._invalid_mask = mask

    def matches_result(self, result):
        return super(NdShallowCache, self).matches_result(result) \
               and result.shape == self.get_value().shape and result.dtype == self.get_value().dtype

    @classmethod
    def create_from_result(cls, result):
        dtype = np.bool_
        if result.dtype.names is not None:
            dtype = [(name, np.bool_) for name in result.dtype.names]
        mask = np.full(result.shape, False, dtype=dtype)
        return cls(result, mask)

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        self._invalid_mask = deep_assign_data_with_paths(self._invalid_mask, path, True)

    def get_uncached_paths(self, path: List[PathComponent]):
        if len(path) > 0 and path[0].references_field_in_field_array():
            return [PathComponent(indexed_cls=np.ndarray, component=path[0].component),
                    PathComponent(indexed_cls=np.ndarray, component=self._invalid_mask[path[0].component])]
        else:
            paths = []
            boolean_mask_of_indices = create_empty_array_with_values_at_indices(
                self._value.shape,
                indices=path[0].component if len(path) > 0 else True,
                value=True,
                empty_value=False
            )

            if self._value.dtype.names:
                for name in self._value.dtype.names:
                    paths.append([PathComponent(indexed_cls=np.ndarray, component=name),
                                  PathComponent(indexed_cls=np.ndarray, component=np.logical_and(
                                      boolean_mask_of_indices,
                                      self._invalid_mask[name]
                                  ))])
            else:
                paths.append(
                    [
                        PathComponent(indexed_cls=np.ndarray,
                                      component=np.logical_and(boolean_mask_of_indices, self._invalid_mask))
                    ]
                )

            return paths


def create_cache(result: Any):
    if isinstance(result, np.ndarray):
        return NdShallowCache.create_from_result(result)
    return ShallowCache(result)


