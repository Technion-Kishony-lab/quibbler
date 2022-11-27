from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, NamedTuple, Any


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


class XY(NamedTuple):
    x: Optional[Any]
    y: Optional[Any]

    @classmethod
    def from_func(cls, func, *args) -> XY:
        """
        Create an XY by apply a func to args two times:
        (1) when any XY arg is replaced with arg.x
        (2) when any XY arg is replaced with arg.y
        """
        x = func(*(arg.x if isinstance(arg, XY) else arg for arg in args))
        y = func(*(arg.y if isinstance(arg, XY) else arg for arg in args))
        return cls(x, y)

    @classmethod
    def from_array_like(cls, array_like) -> XY:
        return cls(array_like[0], array_like[1])

    def is_xor(self) -> bool:
        """
        Return True if only x or only y are defined
        """
        return (self.x is None) ^ (self.y is None)

    def get_xy_not_none(self) -> str:
        """
        Return 'x' if only x is defined, 'y' if only 'y' is defined.
        """
        return 'x' if self.x is not None else 'y'

    def get_value_not_none(self) -> Any:
        """
        Return self.x if only x is defined, self.y if only 'y' is defined.
        """
        return self.x if self.x is not None else self.y


class PointXY(XY):
    def __sub__(self, other) -> PointXY:
        return PointXY(self.x - other.x, self.y - other.y)

    def __mul__(self, other) -> PointXY:
        return PointXY(self.x * other.x, self.y * other.y)

    def __abs__(self) -> PointXY:
        return PointXY(abs(self.x), abs(self.y))

    def __bool__(self) -> bool:
        return not (self.x is None or self.y is None)
