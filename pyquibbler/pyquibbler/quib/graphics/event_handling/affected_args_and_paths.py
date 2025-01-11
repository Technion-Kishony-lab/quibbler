from __future__ import annotations

import numpy as np

from typing import Any, Optional, Tuple, Union

from pyquibbler.path import PathComponent, Path
from pyquibbler.utilities.general_utils import Shape

from .utils import _is_quib

from typing import TYPE_CHECKING

from pyquibbler.utilities.numpy_original_functions import np_shape

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib
    ObjAndPath = Tuple[Union[Quib, Any], Path]


def _get_affected_path_for_plot(shape: Shape, point_index: int, data_index: int):
    if len(shape) == 0:
        return []
    if len(shape) == 1:
        return [PathComponent(point_index)]
    if len(shape) == 2:
        return [
            PathComponent(point_index),
            PathComponent(0 if shape[1] == 1 else data_index)  # de-broadcast if needed
        ]
    assert False, 'Matplotlib is not supposed to support plotting data arguments with >2 dimensions'


def _get_affected_path_for_scatter(shape: Shape, point_index: int):
    if len(shape) == 0:
        return []
    if len(shape) == 1:
        return [PathComponent(np.unravel_index(point_index, shape))]
    assert False, 'Matplotlib is not supposed to support scatter of data arguments with >1 dimensions'


def get_obj_and_path_affected_by_event(arg: Any,
                                        data_index: Optional[int],
                                        picked_index: int) -> Optional[ObjAndPath]:

    if isinstance(arg, list):
        # Legacy. This option is obsolete now that list args of plot are converted to arrays
        maybe_quib = arg[data_index]
        if _is_quib(maybe_quib):
            return maybe_quib, []

    if _is_quib(arg):
        shape = arg.get_shape()
    else:
        shape = np_shape(arg)

    if data_index is None:
        # scatter
        path = _get_affected_path_for_scatter(shape, picked_index)
    else:
        # plot
        path = _get_affected_path_for_plot(shape, picked_index, data_index)
    return arg, path
