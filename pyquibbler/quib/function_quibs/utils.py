from dataclasses import dataclass
from typing import Any, Mapping, Callable, Tuple, Optional

import numpy as np

from ..utils import iter_args_and_names_in_function_call


def create_empty_array_with_values_at_indices(shape: tuple, indices: Any, value: Any,
                                              empty_value: Any = None, dtype=None) -> np.ndarray:
    """
    Create an empty array in a given shape with `values` at `indices`. All other indices will be filled with
    `empty_value`
    """
    res = np.zeros(shape, dtype=dtype or np.array(value).dtype)
    if empty_value is not None:
        res.fill(empty_value)

    res[indices] = value

    return res


@dataclass
class ArgsValues:
    """
    In a function call, when trying to understand what value an a specific parameter was given, looking at
    args and kwargs isn't enough. We have to deal with:
    - Positional arguments passed with a keyword
    - Keyword arguments passed positionally
    - Default arguments
    This class uses the function signature to determine the values each parameter was given,
    and can be indexed using ints, slices and keywords.
    """

    args: Tuple[Any, ...]
    kwargs: Mapping[str, Any]
    arg_values_by_position: Tuple[Any, ...]
    arg_values_by_name: Mapping[str, Any]

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.arg_values_by_name[item]
        return self.arg_values_by_position[item]

    def get(self, keyword: str) -> Optional[Any]:
        return self.arg_values_by_name.get(keyword)

    @classmethod
    def from_function_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], include_defaults):
        try:
            arg_values_by_name = dict(iter_args_and_names_in_function_call(func, args, kwargs, include_defaults))
            arg_values_by_position = tuple(arg_values_by_name.values())
        except ValueError:
            arg_values_by_name = kwargs
            arg_values_by_position = args
        return cls(args, kwargs, arg_values_by_position, arg_values_by_name)
