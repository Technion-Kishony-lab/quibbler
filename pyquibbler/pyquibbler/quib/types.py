from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pytest

from pyquibbler.utilities.numpy_original_functions import np_array


@dataclass
class FileAndLineNumber:
    """
    Points to a specific line number within a specified file.
    """

    file_path: str
    line_no: Optional[int]

    def __repr__(self):
        return f'file: {self.file_path}, line={self.line_no}'

    def _repr_html_(self):
        return f'<a href="file://{self.file_path}">{self}</a>'


class PointArray(np.ndarray):
    def __new__(cls, input_array):
        # Ensure input is a numpy array and shape is (n, 2) or (2,)
        obj = np.asarray(input_array).view(cls)
        cls._check_shape(obj)
        return obj

    @staticmethod
    def _check_shape(obj):
        if obj.ndim == 2 and obj.shape[1] == 2:
            pass
        elif obj.ndim == 1 and obj.shape[0] == 2:
            pass
        else:
            raise ValueError("Input must be a (n, 2) or (2,) array")

    @property
    def x(self):
        if self.ndim == 2:
            return np_array(self[:, 0])
        else:
            return self[0]

    @property
    def y(self):
        if self.ndim == 2:
            return np_array(self[:, 1])
        else:
            return self[1]

    def __bool__(self):
        return bool(self.x) or bool(self.y)

    def __array_finalize__(self, obj):
        # This is called when the object is created or sliced.
        if obj is None:  # If called by __new__, no action needed
            return
        # Ensure slicing preserves the (n, 2) shape constraint
        self._check_shape(obj)


@pytest.mark.parametrize(['point_nd', 'other', 'expected'], [
    (PointArray([[1, 2]]), PointArray([[3, 4]]), PointArray([[4, 6]])),
    (PointArray([[1, 2]]), (3, 4), PointArray([[4, 6]])),
    (PointArray([[1, 2]]), 3, PointArray([[4, 5]])),
])
def test_point_nd_add(point_nd, other, expected):
    result = point_nd + other
    assert np.array_equal(result, expected)
    assert isinstance(result, PointArray)