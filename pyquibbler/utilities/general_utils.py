from __future__ import annotations
from typing import Any, Tuple, Dict

import numpy as np


Args = Tuple[Any, ...]
Kwargs = Dict[str, Any]


def create_empty_array_with_values_at_indices(shape: tuple, indices: Any, value: Any,
                                              empty_value: Any = None, dtype=None) -> np.ndarray:
    """
    Create an empty array in a given shape with `values` at `indices`. All other indices will be filled with
    `empty_value`
    """
    from pyquibbler.quib.factory import get_original_func
    res = get_original_func(np.zeros)(shape, dtype=dtype or get_original_func(np.array)(value).dtype)
    if empty_value is not None:
        res.fill(empty_value)

    res[indices] = value

    return res


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


Shape = Tuple[int, ...]
