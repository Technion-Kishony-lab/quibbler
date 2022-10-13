from dataclasses import dataclass
from typing import Type, Any

import numpy as np

from pyquibbler.utilities.general_utils import Shape


def _get_shape_from_result(result: Any):
    if isinstance(result, np.ndarray):
        return np.shape(result)

    try:
        return np.shape(np.array(result, dtype=object))
    except ValueError:
        if hasattr(result, '__len__'):
            return len(result),
        else:
            return None


@dataclass
class ResultMetadata:
    type: Type
    ndim: int
    shape: Shape

    @classmethod
    def from_result(cls, result):
        type_ = type(result)
        shape = _get_shape_from_result(result)
        ndim = None if shape is None else len(shape)

        return cls(type=type_, shape=shape, ndim=ndim)
