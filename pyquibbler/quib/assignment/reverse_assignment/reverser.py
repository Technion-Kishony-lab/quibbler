from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from operator import getitem
from typing import Any, List, TYPE_CHECKING, Union, Optional

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.assignment import QuibWithAssignment, ReplaceObject
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import iter_quibs_in_object_recursively

if TYPE_CHECKING:
    from pyquibbler.quib import Quib, FunctionQuib


class NoIndicesInAssignmentException(PyQuibblerException):
    pass


@dataclass
class Reversal:
    quib: Quib
    assignments: List[Assignment]


class Reverser(ABC):
    """
    Capable of reverse assigning a function quibs quib arguments given a change in the
    aforementioned function quib's result.
    A particular `Reverser` class knows how to reverse a specific set of functions
    (`SUPPORTED_FUNCTIONS`).
    """

    SUPPORTED_FUNCTIONS: List = NotImplemented

    @classmethod
    def matches(cls, function_quib: FunctionQuib):
        return function_quib.func.__name__ in [supported_func.__name__ for supported_func in cls.SUPPORTED_FUNCTIONS]

    def __init__(self, function_quib: FunctionQuib, assignment: Assignment):
        self._function_quib = function_quib
        self._assignment = assignment

    @lru_cache()
    def _get_quibs_in_args(self) -> List[Quib]:
        """
        Gets a list of all quibs in the args of self._function_quib
        """
        return list(set(iter_quibs_in_object_recursively(self._args)))

    @property
    def _indices(self):
        # If our field is not None, we are representing a structured array that is being changed on it's structured
        # keys. These keys are NOT simply another dimension, and the ndarray's shape is as if without it. Therefore,
        # we attempt to regard the change made as global, and will add the field later on to any paths of
        # assignments we make
        if self._field is not None:
            return True
        return self._assignment.paths[0]

    @property
    def _field(self):
        if len(self._assignment.paths) > 0 and isinstance(self._assignment.paths[0], str):
            return self._assignment.paths[0]
        return None

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
        if self._indices is ReplaceObject:
            # If the entire result has been changed, we can simply return the value
            # as a representation of the whole result (since it IS the whole result)
            return self._value

        return create_empty_array_with_values_at_indices(
            self._function_quib.get_shape().get_value(),
            indices=self._indices,
            value=self._value,
        )

    def _get_new_paths_for_assignment(self, new_indices: Optional[Any] = ReplaceObject):
        """
        Get a list of all new paths necessary for assignment- note that this may not be enough in certain scenarios
        """
        paths = [new_indices, *self._assignment.paths[1:]]
        if self._field is not None:
            # The field we have are relevant for the shape of the quib, but not the field- we need to add the
            # field to the paths. We do want to add it AFTER whichever indexing we did, so that that indexing can
            # continue to be reversed up the quib tree
            paths.insert(1, self._field)
        return paths

    @abstractmethod
    def _get_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        """
        Get all reversals that need to be applied for the reversal to be complete
        (This can potentially contain multiple quibs with multiple assignments)
        """
        pass

    def reverse(self):
        """
        Go through all quibs in args and apply any assignments that need be, given a change in the result of
        a function quib (at self._indices to self._value)
        """
        quibs_with_assignments = self._get_quibs_with_assignments()

        for quib_with_assignment in quibs_with_assignments:
            quib_with_assignment.apply()
