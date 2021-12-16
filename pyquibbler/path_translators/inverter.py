from __future__ import annotations
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional, Callable, Any, Set, Mapping, List, Tuple, Type, TYPE_CHECKING


class Inverter(ABC):

    SUPPORTING_FUNCS: Set[Callable] = set()
    PRIORITY = 0

    @classmethod
    def from_(cls, func_with_args_values, assignment, previouss_result):
        raise NotImplementedError()

    def supports_func(self, func: Callable):
        return func in self.SUPPORTING_FUNCS

    @abstractmethod
    def get_inversals(self):
        pass
