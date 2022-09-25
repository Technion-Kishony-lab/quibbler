from enum import Enum

import numpy as np


class IndexCode(np.int64, Enum):
    """
    Codes for array elements representing a focal source or other objects
    """
    OTHERS_ELEMENT = -6
    NON_CHOSEN_ELEMENT = -5
    SCALAR_NOT_CONTAINING_FOCAL_SOURCE = -4
    SCALAR_CONTAINING_FOCAL_SOURCE = -3
    FOCAL_SOURCE_SCALAR = -2
    CHOSEN_ELEMENT = -1
    # otherwise, source elements are represented by their linear index (int >= 0)


MAXIMAL_NON_FOCAL_SOURCE = IndexCode.SCALAR_NOT_CONTAINING_FOCAL_SOURCE


def _non_focal_source_scalar(containing_focal_source: bool) -> IndexCode:
    return IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE \
        if containing_focal_source \
        else IndexCode.SCALAR_NOT_CONTAINING_FOCAL_SOURCE
