from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Any

from pyquibbler.exceptions import DebugException, PyQuibblerException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


@dataclass
class NestedQuibException(DebugException):
    obj: Any
    nested_quibs: Set[Quib]

    def __str__(self):
        return 'PyQuibbler does not support calling functions with arguments that contain deeply nested quibs.\n' \
               f'The quibs {self.nested_quibs} are deeply nested within {self.obj}.\n'


@dataclass
class LenBoolEtcException(PyQuibblerException, TypeError):
    func_name: str

    def __str__(self):
        func = self.func_name
        return f'{func}(Q), where Q is a quib, is not allowed.\n' \
               f'To create a function quib, use q({func}, Q), or quiby({func})(Q).\n' \
               f'To get the {func} of the current value of Q, use {func}(Q.get_value()).\n'


class CannotIterQuibsException(PyQuibblerException, TypeError):

    def __str__(self):
        return 'Cannot iterate over quibs, as their size can vary.\n' \
               'Try Quib.iter_first(n) to iterate over the n-first items of the quib.\n'


class QuibsShouldPrecedeException(PyQuibblerException, TypeError):

    def __str__(self):
        return '\n' \
               'Binary operators which combine a numpy.ndarray with a quib\n' \
               'are only supported with the quib appearing as the first argument.\n' \
               'For instance, if Q is a quib and A is an array, use `Q + A` rather than `A + Q`.\n' \
               'Or, to implement `A - Q`, use `-Q + A`.\n'


class CannotDisplayQuibWidget(PyQuibblerException):

    def __str__(self):
        return 'Cannot display the quib as a QuibWidget.\n' \
               'To display QuibWidget you must be in Jupyter Lab and with ipywidgets installed.\n'
