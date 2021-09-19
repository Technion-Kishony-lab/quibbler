from typing import Set, List, Any

from .quib import Quib
from .utils import is_there_a_quib_in_object
from ..env import is_debug
from ..exceptions import DebugException


class InputQuib(Quib):
    def __init__(self, artists_redrawers: Set, children: List[Quib], value: Any):
        super().__init__(artists_redrawers, children)
        self._value = value
        if is_debug():
            if is_there_a_quib_in_object(value):
                raise DebugException('Cannot create an input quib that contains another quib')

    @classmethod
    def create(cls, value: Any):
        """
        Public constructor for InputQuib
        """
        return cls(set(), [], value)

    def __setitem__(self, key, value):
        """
        Override data inside the input quib.
        """
        self._value[key] = value
        self.invalidate_and_redraw()

    def get_value(self):
        """
        No need to do any calculation, this is an input quib.
        """
        return self._value

    def _invalidate(self):
        """
        Input quibs are always valid, no need to do anything.
        """
        pass


def iquib(value: Any) -> InputQuib:
    """
    Creates an InputQuib instance containing the given value and return it.
    """
    return InputQuib.create(value)
