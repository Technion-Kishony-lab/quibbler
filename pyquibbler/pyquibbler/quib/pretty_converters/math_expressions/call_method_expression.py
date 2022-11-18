from __future__ import annotations

from dataclasses import dataclass

from pyquibbler.utilities.general_utils import Args, Kwargs
from .func_call_expression import FunctionCallMathExpression
from ..math_precedence import MathPrecedence

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.specialized_functions.quiby_methods import CallObjectMethod


@dataclass
class CallMethodExpression(FunctionCallMathExpression):

    def get_str(self, with_spaces: bool = True):
        obj, *args = self.get_pretty_args()
        return f'{obj}.{self.func_name}({", ".join([*args, *self.get_pretty_kwargs()])})'

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.SUBSCRIPTION


def call_method_converter(func: CallObjectMethod, args: Args, kwargs: Kwargs) -> CallMethodExpression:
    return CallMethodExpression(func_name=func.method,
                                args=args,
                                kwargs=kwargs)
