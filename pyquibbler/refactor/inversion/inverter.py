from __future__ import annotations
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Callable, Any, Set, Mapping, List, Tuple, Type, TYPE_CHECKING


class Inverter(ABC):

    PRIORITY = 0

    def __init__(self, func_call, assignment, previous_result):
        self._func_call = func_call
        self._assignment = assignment
        self._previous_result = previous_result

    @classmethod
    def from_(cls, func_call, assignment, previous_result):
        return cls(func_call, assignment, previous_result)

    @abstractmethod
    def get_inversals(self):
        pass
