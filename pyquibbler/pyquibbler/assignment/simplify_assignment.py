import numpy as np

from typing import Any

from pyquibbler.utilities.numpy_original_functions import np_sum, np_all, np_array

from pyquibbler.path import Path, PathComponent, deep_get

from .assignment import Assignment
from .default_value import default
from .utils import is_integer_scalar, is_array_of_size_one, is_numeric_scalar, convert_array_of_size_one_to_scalar, \
    convert_scalar_value, is_scalar_np


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

        if not (is_array_of_size_one(self.value) or is_scalar_np(self.value) or self.value is default):
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
            self._assignment.value = np_array(self.value, dtype=self.second_to_last_data.dtype)
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
            if isinstance(sub_component, np.ndarray) and sub_component.dtype.type is np.bool_ \
                    and np.shape(sub_component) == (np.shape(self.second_to_last_data)[axis], ):
                if np_sum(sub_component) == 1:
                    new_last_component[axis] = np.where(sub_component)[0].tolist()
                elif np_all(sub_component):
                    new_last_component[axis] = slice(None, None, None)
        self.last_component.component = tuple(new_last_component)

    def _convert_last_sub_components_from_lists_to_arrays(self):
        self.last_component.component = tuple(
            np.array(sub_component) if isinstance(sub_component, list)
            else sub_component for sub_component in self.last_component.component)

    def _convert_last_sub_components_from_arrays_to_lists(self):
        self.last_component.component = tuple(
            sub_component.tolist() if isinstance(sub_component, np.ndarray)
            else sub_component for sub_component in self.last_component.component)

    def _convert_whole_array_bool_indexing(self):
        if len(self.last_component.component) != 1:
            return

        sub_component = self.last_component.component[0]
        data_shape = np.shape(self.second_to_last_data)
        if isinstance(sub_component, np.ndarray) and sub_component.dtype.type is np.bool_ \
                and sub_component.shape == data_shape:
            # whole-array bool indexing
            per_axes_indices = [indices[sub_component] for indices in np.indices(sub_component.shape)]
            for axis, indices in enumerate(per_axes_indices):
                if np.all(indices == indices[0]):
                    per_axes_indices[axis] = indices[0]
                elif np.array_equal(indices, np.arange(data_shape[axis])):
                    per_axes_indices[axis] = slice(None, None, None)
            self.last_component.component = tuple(per_axes_indices)

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

            self._convert_last_sub_components_from_lists_to_arrays()

            self._convert_whole_array_bool_indexing()

            if len(self.last_component.component) == np.ndim(self.second_to_last_data):

                self._convert_bool_indexing()

                self._convert_value_to_match_array_dtype()

                self._convert_value_to_list()

                self._simplify_assignment_of_array_with_size_one()

            self._convert_last_sub_components_from_arrays_to_lists()

            self._convert_tuple_path_component_of_len_1_to_non_tuple()
        except (ValueError, IndexError, TypeError, KeyError):
            pass

        return self._assignment
