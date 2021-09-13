from .quib import Quib
from .utils import is_there_a_quib_in_object
from ..env import is_debug
from ..exceptions import DebugException


class InputQuib(Quib):
    def __init__(self, artists, children, value):
        super().__init__(artists=artists, children=children)
        self._value = value
        if is_debug():
            if is_there_a_quib_in_object(value):
                raise DebugException('Cannot create an input quib that contains another quib')

    def __getitem__(self, item):
        """
        Returns a quib representing the __getitem__ operation, so if this quib is changed,
        whoever called __getitem__ will get the update.
        """
        raise NotImplementedError()

    def __setitem__(self, key, value):
        """
        Override data inside the input quib.
        """
        self._value[key] = value
        self._invalidate_and_redraw()

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


def iquib(value):
    """
    Creates an input quib containing the given value and return it.
    """
    return InputQuib(set(), [], value)
