from enum import Enum

import numpy as np
from numpy.typing import NDArray


class IndexCode(np.int64, Enum):
    """
    Codes for array elements representing a focal source or other objects
    """
    OTHERS_ELEMENT = -7
    NON_CHOSEN_ELEMENT = -6
    SCALAR_NOT_CONTAINING_FOCAL_SOURCE = -5
    LIST_NOT_CONTAINING_CHOSEN_ELEMENTS = -4
    LIST_CONTAINING_CHOSEN_ELEMENTS = -3
    SCALAR_CONTAINING_FOCAL_SOURCE = -2
    FOCAL_SOURCE_SCALAR = -1
    # otherwise, source elements are represented by their linear index (np.int64 >= 0)


MAXIMAL_NON_CHOSEN_ELEMENTS = IndexCode.LIST_NOT_CONTAINING_CHOSEN_ELEMENTS


def is_focal_element(obj: NDArray):
    return obj > MAXIMAL_NON_CHOSEN_ELEMENTS
