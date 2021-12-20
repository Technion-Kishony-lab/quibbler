from dataclasses import dataclass
from typing import Any, Mapping, Callable, Tuple, Optional, Dict

import numpy as np

from .external_call_failed_exception_handling import external_call_failed_exception_handling
from ..utils import iter_args_and_names_in_function_call

Args = Tuple[Any, ...]
Kwargs = Dict[str, Any]


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
        from ...overriding.types import KeywordArgument, IndexArgument

        if isinstance(item, KeywordArgument):
            return self.arg_values_by_name[item.keyword]
        elif isinstance(item, IndexArgument):
            return self.arg_values_by_position[item.index]

        # TODO: Is following necessary? Primitive obssession..
        if isinstance(item, str):
            return self.arg_values_by_name[item]
        return self.arg_values_by_position[item]

    def get(self, keyword: str, default: Optional = None) -> Optional[Any]:
        return self.arg_values_by_name.get(keyword, default)

    @classmethod
    def from_function_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], include_defaults):
        # We use external_call_failed_exception_handling here as if the user provided the wrong arguments to the
        # function we'll fail here

        from pyquibbler.overriding.utils import get_original_func_from_partialled_func
        func = get_original_func_from_partialled_func(func)

        with external_call_failed_exception_handling():
            try:
                arg_values_by_name = dict(iter_args_and_names_in_function_call(func, args, kwargs, include_defaults))
                arg_values_by_position = tuple(arg_values_by_name.values())
            except ValueError:
                arg_values_by_name = kwargs
                arg_values_by_position = args

        return cls(args, kwargs, arg_values_by_position, arg_values_by_name)


@dataclass
class FuncWithArgsValues:
    args_values: ArgsValues
    func: Callable

    @classmethod
    def from_function_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], include_defaults):
        return cls(args_values=ArgsValues.from_function_call(func, args, kwargs, include_defaults), func=func)


def unbroadcast_bool_mask(bool_mask: np.ndarray, original_shape: Tuple[int, ...]) -> np.ndarray:
    """
    Given a bool mask representing changes in an array which is a result of a broadcast, return an "un-broadcast"
    array in the given original shape (the shape before broadcasting) in which each boolean is true
    if any of its broadcast bools was true.
    """
    new_broadcast_ndim = bool_mask.ndim - len(original_shape)
    assert new_broadcast_ndim >= 0
    new_broadcast_axes = tuple(range(0, new_broadcast_ndim))
    reduced_bool_mask = np.any(bool_mask, axis=new_broadcast_axes)
    broadcast_loop_dimensions_to_reduce = tuple(i for i, (result_len, quib_len) in
                                                enumerate(zip(reduced_bool_mask.shape, original_shape))
                                                if result_len != quib_len)
    reduced_bool_mask = np.any(reduced_bool_mask, axis=broadcast_loop_dimensions_to_reduce, keepdims=True)
    return np.broadcast_to(reduced_bool_mask, original_shape)


def convert_args_and_kwargs(converter: Callable, args: Args, kwargs: Kwargs):
    """
    Apply the given converter on all given arg and kwarg values.
    """
    return (tuple(converter(i, val) for i, val in enumerate(args)),
            {name: converter(name, val) for name, val in kwargs.items()})
