from typing import Callable, Any, Tuple, Mapping

import numpy as np

from pyquibbler import Assignment
from pyquibbler.inversion.invert import invert
from pyquibbler.translation.utils import call_func_with_values
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_in_path


def inverse(func: Callable, indices: Any, value: Any, args: Tuple[Any, ...] = None, kwargs: Mapping[str, Any] = None,
            empty_path: bool = False):
    # if hasattr(func, '__wrapped__') and func.__wrapped__:
    #     func = func.__wrapped__
    if indices is not None and empty_path is True:
        raise Exception("The indices cannot be set if empty path is True")

    args = args or tuple()
    kwargs = kwargs or {}
    previous_value = call_func_with_values(func, args, kwargs)
    inversals = invert(
        func=func,
        args=args,
        kwargs=kwargs,
        previous_result=previous_value,
        assignment=Assignment(path=[PathComponent(indexed_cls=np.ndarray, component=indices)] if not empty_path else [],
                              value=value)
    )

    return {
        inversal.source: deep_assign_data_in_path(inversal.source.value,
                                                  inversal.assignment.path,
                                                  inversal.assignment.value)
        for inversal in inversals
    }