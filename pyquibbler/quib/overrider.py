import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Tuple, List


class Overrider(ABC):
    @abstractmethod
    def add_override(self, key: Any, value: Any):
        """
        Adds an override to the overrider - data[key] = value.
        """

    @abstractmethod
    def override(self, data: Any):
        """
        Applies all overrides to the given data.
        """


class ObjectOverrider(Overrider):
    def __init__(self):
        self._overrides: List[Tuple[Any, Any]] = []

    def add_override(self, key: Any, value: Any):
        self._overrides.append((key, value))

    def override(self, data: Any):
        for key, value in self._overrides:
            self._overrides[key] = value

    def apply_to_overrider(self, overrider: Overrider):
        """
        Applies all overrides to another overrider object.
        """
        for key, value in self._overrides:
            overrider.add_override(key, value)


class NdArrayOverrider(Overrider):
    def __init__(self, shape: Tuple[int, ...], dtype: np.dtype):
        self._override_mask = np.zeros(shape, dtype=np.bool)
        self._override_arr = np.zeros(shape, dtype=dtype)

    @classmethod
    def from_ndarray(cls, arr: np.ndarray):
        return cls(arr.shape, arr.dtype)

    def add_override(self, key: Any, value: Any):
        self._override_mask[key] = True
        self._override_arr[key] = value

    def override(self, data: Any):
        data[self._override_mask] = self._override_arr
