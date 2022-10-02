from typing import Any, Type, Union, Tuple

import numpy as np

from pyquibbler.path import Path


def working_component(path: Path):
    """
    Get the first working component value you can from the path- this will always be entirely "squashed", so you will
    get a component that expresses everything possible before needing to go another step "deeper" in

    If no component is found (path is empty), the path expresses getting "everything"- so we give a true value
    """
    return path[0].component if len(path) > 0 else True


def working_component_of_type(path: Path, separate: bool):
    return (path[0].component, path[1:]) if len(path) > 0 and separate else (True, path)


def translate_bool_vector_to_slice_if_possible(bool_index: bool) -> Union[None, slice]:
    indices, = np.nonzero(bool_index)
    if len(indices) == 0:
        return slice(0, 0)
    if len(indices) == 1:
        return slice(indices[0], indices[0] + 1)

    diff_indices = np.diff(indices)
    if np.all(diff_indices == diff_indices[0]):
        return slice(indices[0], indices[-1] + 1, diff_indices[0])
    return None
