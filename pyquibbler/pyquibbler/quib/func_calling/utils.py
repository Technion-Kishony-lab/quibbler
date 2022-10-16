from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Tuple, Any, Dict


from typing import TYPE_CHECKING

from pyquibbler.utilities.general_utils import Args, Kwargs

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


def convert_args_and_kwargs(converter: Callable, args: Args, kwargs: Kwargs):
    """
    Apply the given converter on all given arg and kwarg values.
    """
    return (tuple(converter(i, val) for i, val in enumerate(args)),
            {name: converter(name, val) for name, val in kwargs.items()})


def get_shape_from_result(result: Any):
    if isinstance(result, np.ndarray):
        return np.shape(result)

    try:
        return np.shape(np.array(result, dtype=object))
    except ValueError:
        if hasattr(result, '__len__'):
            return len(result),
        else:
            return None
