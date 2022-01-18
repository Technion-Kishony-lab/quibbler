from __future__ import annotations
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Tuple, Any, Dict, TYPE_CHECKING

import numpy as np

from pyquibbler.path import Path
from pyquibbler.utilities.iterators import recursively_run_func_on_object

if TYPE_CHECKING:
    from pyquibbler.quib.func_calling.quib_func_call import QuibFuncCall


@dataclass(frozen=True)
class CachedCall:
    func: Callable
    args: Tuple[Any, ...]
    kwargs: Tuple[Tuple[str, Any], ...]

    @classmethod
    def create(cls, func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]):
        return cls(func, args, tuple(kwargs.items()))


def cache_method_until_full_invalidation(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self: QuibFuncCall, *args, **kwargs):
        call = CachedCall.create(func, args, kwargs)
        if call in self.method_cache:
            return self.method_cache[call]
        result = func(self, *args, **kwargs)
        self.method_cache[call] = result
        return result

    return wrapper


def create_array_from_func(func, shape):
    return np.vectorize(lambda _: func(), otypes=[object])(np.empty(shape))


def proxify_args(args, kwargs):
    from pyquibbler.quib import Quib
    quibs_to_guard = set()

    def _replace_quibs_with_proxy_quibs(arg):
        if isinstance(arg, Quib):
            from pyquibbler.quib.specialized_functions.proxy import create_proxy
            proxy = create_proxy(arg)
            quibs_to_guard.add(proxy)
            return proxy
        return arg

    args = recursively_run_func_on_object(_replace_quibs_with_proxy_quibs, args)
    kwargs = {k: recursively_run_func_on_object(_replace_quibs_with_proxy_quibs, v) for k, v in kwargs.items()}
    return args, kwargs, quibs_to_guard
