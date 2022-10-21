from __future__ import annotations

import numpy as np
from functools import wraps

from typing import Callable, Any
from pyquibbler.utilities.general_utils import Args, Kwargs

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.func_calling.quib_func_call import QuibFuncCall


def cache_method_until_full_invalidation(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self: QuibFuncCall):
        if func in self.method_cache:
            return self.method_cache[func]
        result = func(self)
        self.method_cache[func] = result
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
        return np.shape(np.asarray(result, dtype=object))
    except ValueError:
        if hasattr(result, '__len__'):
            return len(result),
        else:
            return None
