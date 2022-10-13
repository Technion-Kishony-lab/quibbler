import numpy as np

from typing import Any
from .assignment import Assignment
from .default_value import default
from .utils import is_integer_scalar, is_array_of_size_one, is_numeric_scalar, convert_array_of_size_one_to_scalar, \
    convert_scalar_value
from ..path import Path, PathComponent, deep_get


class AssignmentSimplifier:
    """
    Takes an Assignment into some data object and simplifies the assignment
    so that it is easier to read as text.
    """
    def __init__(self, assignment: Assignment, data: Any):
        self._assignment = assignment
        self._data = data

    def get_assignment(self):
        return self._assignment

    @property
    def path(self) -> Path:
        return self._assignment.path

    @property
    def last_component(self) -> PathComponent:
        return self._assignment.path[-1]

    @property
    def second_to_last_data(self) -> Any:
        return deep_get(self._data, self.path[:-1])

    @property
    def last_data(self) -> Any:
        return deep_get(self._data, self.path)

    @property
    def value(self):
        return self._assignment.value

    def _make_last_component_tuple(self):
        if not isinstance(self.last_component.component, tuple):
            self.last_component.component = (self.last_component.component,)

    def _simplify_assignment_of_array_with_size_one(self):
        if not all(is_array_of_size_one(index) or is_integer_scalar(index) for index in self.last_component.component):
            return

        if not (is_array_of_size_one(self.value) or is_numeric_scalar(self.value) or self.value is default):
            return

        self.last_component.component = \
            tuple(convert_array_of_size_one_to_scalar(index) for index in self.last_component.component)
        self._assignment.value = convert_array_of_size_one_to_scalar(self._assignment.value)

    def _convert_tuple_path_component_of_len_1_to_non_tuple(self):
        if len(self.last_component.component) == 1:
            self.last_component.component = self.last_component.component[0]

    def _convert_value_to_match_array_dtype(self):
        if not isinstance(self.second_to_last_data, np.ndarray):
            return

        if isinstance(self.value, np.ndarray):
            self._assignment.value = np.array(self.value, dtype=self.second_to_last_data.dtype)
        elif self.value is not default:
            try:
                self._assignment.value = self.second_to_last_data.dtype.type(self.value)
            except ValueError:
                pass

    def _convert_value_to_list(self):
        if not (isinstance(self.second_to_last_data, np.ndarray) and isinstance(self._assignment.value, np.ndarray)):
            return

        self._assignment.value = self._assignment.value.tolist()

    def _convert_bool_indexing(self):
        new_last_component = list(self.last_component.component)
        for axis, sub_component in enumerate(self.last_component.component):
            if isinstance(sub_component, list):
                sub_component = np.array(sub_component)
            if not isinstance(sub_component, np.ndarray):
                continue
            if sub_component.dtype.type is np.bool_ \
                    and np.shape(sub_component) == (np.shape(self.second_to_last_data)[axis], ):
                if np.sum(sub_component) == 1:
                    new_last_component[axis] = np.where(sub_component)[0].tolist()
                elif np.all(sub_component):
                    new_last_component[axis] = slice(None, None, None)
        self.last_component.component = tuple(new_last_component)

    def simplify(self) -> Assignment:
        """
        Call this method to get the simplified assignment.
        """

        try:
            if is_numeric_scalar(self.last_data) and is_numeric_scalar(self.value):
                self._assignment.value = convert_scalar_value(self.last_data, self.value)

            if len(self.path) == 0 or not isinstance(self.second_to_last_data, (np.ndarray, list)) \
                    or isinstance(self.last_component.component, str):
                return self._assignment

            self._make_last_component_tuple()

            if len(self.last_component.component) == np.ndim(self.second_to_last_data):

                self._convert_bool_indexing()

                self._convert_value_to_match_array_dtype()

                self._convert_value_to_list()

                self._simplify_assignment_of_array_with_size_one()

            self._convert_tuple_path_component_of_len_1_to_non_tuple()
        except (ValueError, IndexError, TypeError, KeyError):
            pass

        return self._assignment
