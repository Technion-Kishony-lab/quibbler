from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .quib import Quib


@dataclass
class QuibRef:
    """
    Wraps a quib when passed as an argument to a quib-supporting function,
    in order to signal that the function expects the quib itself and not its value.
    """
    quib: Quib
