from __future__ import annotations

import numpy as np

from typing import Any, Optional, Tuple

from pyquibbler.path import PathComponent, Path
from pyquibbler.utilities.general_utils import Shape

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib
    QuibAndPath = Tuple[Quib, Path]


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


def get_quib_and_path_affected_by_event(arg: Any,
                                        data_index: Optional[int],
                                        picked_index: int) -> Optional[QuibAndPath]:
    from pyquibbler.quib.quib import Quib
    if isinstance(arg, Quib):
        shape = arg.get_shape()
        if data_index is None:
            # scatter
            path = _get_affected_path_for_scatter(shape, picked_index)
        else:
            # plot
            path = _get_affected_path_for_plot(shape, picked_index, data_index)
        return arg, path

    # Legacy code. This option is obsolete now that list args of plot are converted to arrays
    if isinstance(arg, list):
        quib = arg[data_index]
        if isinstance(quib, Quib):
            return quib, []

    return None
