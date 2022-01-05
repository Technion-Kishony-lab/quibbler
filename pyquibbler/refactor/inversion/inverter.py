from __future__ import annotations
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Callable, Any, Set, Mapping, List, Tuple, Type, TYPE_CHECKING

from pyquibbler.refactor.quib.assignment.utils import deep_assign_data_in_path
from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.refactor.func_call import FuncCall


class Inverter(ABC):

    PRIORITY = 0

    def __init__(self, func_call: FuncCall, assignment, previous_result):
        self._func_call = func_call
        self._assignment = assignment
        self._previous_result = previous_result

    @classmethod
    def from_(cls, func_call, assignment, previous_result):
        return cls(func_call, assignment, previous_result)

    @abstractmethod
    def get_inversals(self):
        pass

    def _get_result_with_assignment_set(self):
        # TODO: Implement a deep copy that is agnostic to quibs!
        new_result = deep_copy_without_quibs_or_graphics(self._previous_result)
        return deep_assign_data_in_path(new_result, self._assignment.path, self._assignment.value)

