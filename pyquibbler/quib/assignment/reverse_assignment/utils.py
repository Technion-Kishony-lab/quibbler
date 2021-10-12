from typing import Any, List, Tuple

import numpy as np

from pyquibbler.quib.assignment.assignment import PathComponent


def create_empty_array_with_values_at_indices(shape: tuple, indices: Any, value: Any,
                                              empty_value: Any = None, dtype=None) -> np.ndarray:
    """
    Create an empty array in a given shape with `values` at `indices`. All other indices will be filled with
    `empty_value`
    """
    from pyquibbler.quib.assignment.overrider import deep_assign_data_with_paths
    res = np.zeros(shape, dtype=dtype or np.array(value).dtype)
    if empty_value is not None:
        res.fill(empty_value)

    res[indices] = value

    return res


def deep_get_until_field(data: Any, path: List[PathComponent]):
    for component in path:
        if isinstance(component, str):
            return data
        data = data[component]
    return data


def deep_get(data: Any, path: List[PathComponent]):
    for component in path:
        data = data[component]
    return data

def squash_path(shape: Tuple, path: List[PathComponent]):
    pass
