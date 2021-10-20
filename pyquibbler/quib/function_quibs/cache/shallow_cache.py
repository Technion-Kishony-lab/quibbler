from functools import wraps
from typing import List, Any, Optional, Type

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path


class Invalid:
    pass


invalid = Invalid()


class PathCannotHaveComponentsException(PyQuibblerException):

    def __str__(self):
        return "This shallow cache does not support specifying paths that are not `all` (ie `[]`)"


class ShallowCache:

    SUPPORTING_TYPES = (object,)

    def __init__(self, value: Any):
        self._value = value

    @classmethod
    def create_from_result(cls, result):
        # We always start completely invalid
        return cls(invalid)

    def matches_result(self, result):
        return isinstance(result, self.SUPPORTING_TYPES)

    def set_valid_value_at_path(self, path: List[PathComponent], value: Any) -> None:
        if len(path) != 0:
            raise PathCannotHaveComponentsException()
        self._value = value

    def set_invalid_at_path(self, path: List[PathComponent]) -> None:
        if len(path) != 0:
            raise PathCannotHaveComponentsException()
        self._value = invalid

    def get_uncached_paths(self, path):
        if self._value is invalid:
            return [path]
        return []

    def get_value(self) -> Any:
        return self._value



