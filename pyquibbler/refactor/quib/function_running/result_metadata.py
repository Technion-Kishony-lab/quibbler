from dataclasses import dataclass
from typing import Type, Any

import numpy as np

from pyquibbler.refactor.utilities.general_utils import Shape


def _get_shape_from_result(result: Any):
    try:
        shape = np.shape(result)
    except ValueError:
        if hasattr(result, '__len__'):
            shape = len(result),
        else:
            shape = None
    return shape


@dataclass
class ResultMetadata:
    type: Type
    ndim: int
    shape: Shape

    @classmethod
    def from_result(cls, result):
        type_ = type(result)

        shape = _get_shape_from_result(result)

        if shape:
            ndim = len(shape)
        else:
            ndim = None

        return cls(type=type_, shape=shape, ndim=ndim)
