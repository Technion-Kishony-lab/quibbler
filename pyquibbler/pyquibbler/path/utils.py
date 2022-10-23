import copy
from typing import Any, Union, Tuple

import numpy as np

from .path_component import Path, PathComponent, SpecialComponent
from .data_accessing import deep_get


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


def squash_path(path: Path) -> Path:
    if len(path) == 0:
        return []
    return [PathComponent(tuple(c.component for c in path))]


def split_path_at_end_of_object(obj: Any, path: Path) -> Tuple[Path, Path, Any]:
    """
    Split the path into the part that reference within the given object (upto a final unbreakable object element),
    and the remaining part of the path.
    We also take care of cases where say a 2-dimensional array was collapsed into a 1-dimensional object array of list
    yet is still referenced as obj[cmp1, cmp2]
    """

    path_within_object = []
    remaining_path = copy.copy(path)
    for cmp in path:
        try:
            obj = deep_get(obj, [cmp])
        except Exception:
            if cmp.is_compound():
                broken_path = cmp.get_multi_step_path()
                broken_path_to_end, broken_path_after, obj = split_path_at_end_of_object(obj, broken_path)
                broken_path_to_end = squash_path(broken_path_to_end)
                broken_path_after = squash_path(broken_path_after)
                path_within_object += broken_path_to_end
                remaining_path.pop(0)
                remaining_path = broken_path_after + remaining_path
            break
        path_within_object.append(cmp)
        remaining_path.pop(0)
    if len(path_within_object) == 0:
        path_within_object = [PathComponent(SpecialComponent.ALL)]
    return path_within_object, remaining_path, obj
