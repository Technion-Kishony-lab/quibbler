from typing import Any

import numpy as np


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
