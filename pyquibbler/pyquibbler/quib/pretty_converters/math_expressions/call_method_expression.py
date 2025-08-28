from __future__ import annotations

from dataclasses import dataclass

from .func_call_expression import FunctionCallMathExpression
from ..math_precedence import MathPrecedence


@dataclass
class CallMethodExpression(FunctionCallMathExpression):

    def get_str(self, with_spaces: bool = True):
        obj, *args = self.get_pretty_args()
        return f'{(obj)}.{self.func_name}({", ".join([*args, *self.get_pretty_kwargs()])})'

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.SUBSCRIPTION
