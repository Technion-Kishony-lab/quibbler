from __future__ import annotations
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Tuple, Any, Dict, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pyquibbler.refactor.quib.function_running.function_runner import FunctionRunner


@dataclass(frozen=True)
class FunctionCall:
    func: Callable
    args: Tuple[Any, ...]
    kwargs: Tuple[Tuple[str, Any], ...]

    @classmethod
    def create(cls, func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]):
        return cls(func, args, tuple(kwargs.items()))


def cache_method_until_full_invalidation(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self: FunctionRunner, *args, **kwargs):
        call = FunctionCall.create(func, args, kwargs)
        if call in self.method_cache:
            return self.method_cache[call]
        result = func(self, *args, **kwargs)
        self.method_cache[call] = result
        return result

    return wrapper


def create_array_from_func(func, shape):
    return np.vectorize(lambda _: func(), otypes=[object])(np.empty(shape))
