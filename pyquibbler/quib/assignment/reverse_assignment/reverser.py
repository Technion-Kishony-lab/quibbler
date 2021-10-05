from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, List, TYPE_CHECKING, Union, Optional, Callable

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.assignment import QuibWithAssignment
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import iter_quibs_in_object_recursively

if TYPE_CHECKING:
    from pyquibbler.quib import Quib, FunctionQuib


class NoIndicesInAssignmentException(PyQuibblerException):
    pass


class Reverser(ABC):
    """
    Capable of reverse assigning a function quibs quib arguments given a change in the
    aforementioned function quib's result.
    A particular `Reverser` class knows how to reverse a specific set of functions
    (`SUPPORTED_FUNCTIONS`).
    """

    SUPPORTED_FUNCTIONS: List[Callable] = NotImplemented

    def __init__(self, function_quib: FunctionQuib, assignment: Assignment):
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
        return self._assignment.paths[0]

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

    def reverse(self):
        """
        Go through all quibs in args and apply any assignments that need be, given a change in the result of
        a function quib (at self._indices to self._value)
        """
        quibs_with_assignments = self.get_quibs_with_assignments()

        for quib_with_assignment in quibs_with_assignments:
            quib_with_assignment.apply()

