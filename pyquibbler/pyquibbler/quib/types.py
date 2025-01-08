from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np

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


PointArray = np_array
