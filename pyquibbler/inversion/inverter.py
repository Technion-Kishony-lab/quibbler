from __future__ import annotations
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Callable, Any, Set, Mapping, List, Tuple, Type, TYPE_CHECKING


class Inverter(ABC):

    SUPPORTING_FUNCS: Set[Callable] = set()
    PRIORITY = 0

    def __init__(self, func_with_args_values, assignment, previous_result):
        self._func_with_args_values = func_with_args_values
        self._assignment = assignment
        self._previous_result = previous_result

    @classmethod
    def from_(cls, func_with_args_values, assignment, previous_result):
        return cls(func_with_args_values, assignment, previous_result)

    def supports_func(self, func: Callable):
        return func in self.SUPPORTING_FUNCS

    @abstractmethod
    def get_inversals(self):
        pass
