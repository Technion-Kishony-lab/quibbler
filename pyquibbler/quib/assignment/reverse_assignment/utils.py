from typing import Any

import numpy as np


def create_empty_array_with_values_at_indices(shape: tuple, indices: Any, value: Any,
                                              empty_value: Any = 0) -> np.ndarray:
    """
    Create an empty array in a given shape with `values` at `indices`. All other indices will be filled with
    `empty_value`
    """
    res = np.full(shape, empty_value)
    res[indices] = value
    return res

