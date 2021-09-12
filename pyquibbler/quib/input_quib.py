from .quib import Quib


class InputQuib(Quib):
    def __init__(self, artists, children, value):
        super().__init__(artists=artists, children=children)
        self._value = value

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
    return InputQuib(set(), [], value)
