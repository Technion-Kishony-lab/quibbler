from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, List


from pyquibbler.quib import Quib, FunctionQuib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.utils import iter_quibs_in_object_recursively


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

    SUPPORTED_FUNCTIONS = NotImplemented

    @classmethod
    def matches(cls, function_quib: FunctionQuib):
        return function_quib.func in cls.SUPPORTED_FUNCTIONS

    def __init__(self, function_quib: FunctionQuib, indices: Any, value: Any):
        self._function_quib = function_quib
        self._indices = indices
        self._value = value

    @lru_cache()
    def _get_quibs_in_args(self) -> List[Quib]:
        """
        Gets a list of all quibs in the args of self._function_quib
        """
        return list(set(iter_quibs_in_object_recursively(self._args)))

    @property
    def _func(self):
        return self._function_quib.func

    @property
    def _args(self):
        return self._function_quib.args

    @property
    def _kwargs(self):
        return self._function_quib.kwargs

    @abstractmethod
    def _get_reversals(self) -> List[Reversal]:
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
        reversals = self._get_reversals()
        for reversal in reversals:
            for assignment in reversal.assignments:
                reversal.quib.assign(value=assignment.value, indices=assignment.key)
