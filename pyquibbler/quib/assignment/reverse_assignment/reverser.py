from __future__ import annotations

import functools

import numpy as np
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, List, TYPE_CHECKING, Union, Callable

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.assignment import QuibWithAssignment, PathComponent
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices, deep_get
from pyquibbler.quib.utils import iter_quibs_in_object_recursively

if TYPE_CHECKING:
    from pyquibbler.quib import Quib, FunctionQuib


class Reverser(ABC):
    """
    Capable of reverse assigning a function quibs quib arguments given a change in the
    aforementioned function quib's result.
    A particular `Reverser` class knows how to reverse a specific set of functions
    (`SUPPORTED_FUNCTIONS`).
    """

    SUPPORTED_FUNCTIONS: List[Callable] = NotImplemented

    def __init__(self, function_quib, assignment: Assignment):
        self._function_quib = function_quib
        self._assignment = assignment

    @lru_cache()
    def _get_quibs_in_args(self) -> List[Quib]:
        """
        Gets a list of all unique quibs in the args of self._function_quib
        """
        quibs = []
        for quib in iter_quibs_in_object_recursively(self._args):
            if quib not in quibs:
                quibs.append(quib)

        return quibs

    @property
    def _working_indices(self):
        """
        Our working indices, ie the ones that need to be either squashed
        :return:
        """
        return self._assignment.path[0].component

    @property
    def _value(self):
        return self._assignment.value

    @property
    def _func(self):
        return self._function_quib.func

    @property
    def _args(self):
        return self._function_quib.args

    @property
    def _kwargs(self):
        return self._function_quib.kwargs

    def _get_representative_function_quib_result_with_value(self) -> Union[np.ndarray, Any]:
        """
        Since we don't have the real result (may not have been computed yet),
        we create a representative result in same shape as the real result and set the new value in it
        """
        return create_empty_array_with_values_at_indices(
            self._function_quib.get_shape().get_value(),
            indices=self._working_indices,
            value=self._value,
        )

    @abstractmethod
    def get_reversed_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        """
        Get all reversals that need to be applied for the reversal to be complete
        (This can potentially contain multiple quibs with multiple assignments)
        """
        pass

    @classmethod
    def create_and_get_reversed_quibs_with_assignments(cls, function_quib: 'FunctionQuib', assignment: Assignment):
        components_at_end = assignment.path[1:]
        current_path = assignment.path[0]

        # There is a specific scenario in which we have a numpy function that returns an numpy array which is
        # referenced by fields- this cannot happen with PyObject arrays, only with field arrays, as a PyObject array
        # cannot be immediately referenced by an inner attribute/indexing method without first accessing the numpy array
        #
        # If we're setting a field, we want to emulate the function having replaced the entire object instead of just the
        # referenced field (so we can do any index + quib choosing games);
        # then when we add in the field in the path after it the overrider will create the desired affect
        # of only changing the referenced field
        if assignment.path[0].references_field_in_field_array():
            components_at_end = [assignment.path[0], *components_at_end]
            current_path = PathComponent(indexed_cls=np.ndarray, component=...)

        reverser = cls(function_quib, Assignment(assignment.value, [current_path]))
        quibs_with_assignments = reverser.get_reversed_quibs_with_assignments()

        for quib_with_assignment in quibs_with_assignments:
            quib_with_assignment.assignment.path.extend(components_at_end)

        return quibs_with_assignments
