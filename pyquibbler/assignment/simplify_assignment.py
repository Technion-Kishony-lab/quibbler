import numpy as np

from typing import Any
from .assignment import Assignment


def is_scalar(data) -> bool:
    return not isinstance(data, (list, tuple, np.ndarray))


def is_array_of_size_one(data) -> bool:
    return isinstance(data, np.ndarray) and data.size == 1 \
           or isinstance(data, list) and len(data) == 1


def convert_array_of_size_one_to_scalar(data):
    if is_array_of_size_one(data):
        return data[0]
    return data


class AssignmentSimplifier:

    def __init__(self, assignment: Assignment, data: Any):
        self._assignment = assignment
        self._data = data

    def get_assignment(self):
        return self._assignment

    @property
    def path(self):
        return self._assignment.path

    @property
    def value(self):
        return self._assignment.value

    def _make_first_component_tuple(self):
        if not isinstance(self.path[0].component, tuple):
            self.path[0].component = (self.path[0].component,)

    def _simplify_assignment_of_array_with_size_one(self):
        if len(self.path) != 1:
            return

        if len(self.path[0].component) != np.ndim(self._data):
            return

        if not all(is_array_of_size_one(index) or is_scalar(index) for index in self.path[0].component):
            return

        if not (is_array_of_size_one(self.value) or is_scalar(self.value)):
            return

        self.path[0].component = tuple(convert_array_of_size_one_to_scalar(index) for index in self.path[0].component)
        self._assignment.value = convert_array_of_size_one_to_scalar(self._assignment.value)

    def _convert_tuple_path_component_of_len_1_to_non_tuple(self):
        if len(self.path[0].component) == 1:
            self.path[0].component = self.path[0].component[0]

    def simplify(self) -> Assignment:

        path = self.path

        if len(path) == 0:
            return self._assignment

        self._make_first_component_tuple()

        self._simplify_assignment_of_array_with_size_one()

        self._convert_tuple_path_component_of_len_1_to_non_tuple()

        return self._assignment
