from __future__ import annotations
from typing import Any, Tuple, Dict, List
from numpy.typing import NDArray, ArrayLike

from pyquibbler.path import deep_set, PathComponent, Path
from pyquibbler.utilities.numpy_original_functions import np_zeros

import numpy as np


Args = Tuple[Any, ...]
Kwargs = Dict[str, Any]
Shape = Tuple[int, ...]


def create_bool_mask_with_true_at_path(shape: Shape, path: Path) -> NDArray[bool]:
    """
    Create an array of False in a given shape with True at the given `path`.
    """
    res = np_zeros(shape, dtype=bool)
    deep_set(res, path, True, should_copy_objects_referenced=False)
    return res


def create_bool_mask_with_true_at_indices(shape: Shape, indices: Any) -> NDArray[bool]:
    """
    Create an array of False in a given shape with True at `indices`.
    """
    return create_bool_mask_with_true_at_path(shape, [PathComponent(indices)])


def unbroadcast_or_broadcast_bool_mask(bool_mask: np.ndarray, original_shape: Shape) -> NDArray:
    """
    Given a bool mask representing changes in an array which is a result of a broadcast, return an "un-broadcast"
    array in the given original shape (the shape before broadcasting) in which each boolean is true
    if any of its broadcast bools was true.

    If array has less dimensions than the original_shape, then we broadcast instead of unbroadcast.
    """
    new_broadcast_ndim = bool_mask.ndim - len(original_shape)
    if new_broadcast_ndim < 0:
        return np.broadcast_to(bool_mask, original_shape)
    new_broadcast_axes = tuple(range(0, new_broadcast_ndim))
    reduced_bool_mask = np.any(bool_mask, axis=new_broadcast_axes)
    broadcast_loop_dimensions_to_reduce = tuple(i for i, (result_len, quib_len) in
                                                enumerate(zip(reduced_bool_mask.shape, original_shape))
                                                if result_len != quib_len)
    reduced_bool_mask = np.any(reduced_bool_mask, axis=broadcast_loop_dimensions_to_reduce, keepdims=True)
    return np.broadcast_to(reduced_bool_mask, original_shape)


def is_object_array(obj):
    """
    Check if obj is an array of objects
    """
    return isinstance(obj, np.ndarray) and obj.dtype.type is np.object_


def is_non_object_array(obj):
    """
    Check if obj is a normal array (non object)
    """
    return isinstance(obj, np.ndarray) and obj.dtype.type is not np.object_


def is_same_shapes(args: List[ArrayLike]) -> bool:
    """
    Check if all elements of args have the same shape
    """
    if len(args) <= 1:
        return True

    return all(np.shape(arg) == np.shape(args[0]) for arg in args)


def get_shared_shape(args: List[ArrayLike]) -> Shape:
    """
    Get the shape in the first dimensions which are shared by all args
    """
    if len(args) == 0:
        return tuple()

    shapes = list(map(np.shape, args))
    shape0 = shapes[0]
    min_dim = min(map(len, shapes))

    if min_dim == 0:
        return tuple()

    for i in range(min_dim):
        if not all(shape[i] == shape0[i] for shape in shapes):
            return shape0[:i]
    return shape0[:i + 1]
