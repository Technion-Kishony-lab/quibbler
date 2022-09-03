from dataclasses import dataclass
from typing import Any, Tuple

from ..math_precedence import MathPrecedence
from .math_expression import MathExpression

SPACE = ' '


@dataclass
class NameMathExpression(MathExpression):
    name: str

    def get_str(self, with_spaces: bool = True):
        return self.name

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.VAR_NAME_WITH_SPACES if SPACE in self.name else MathPrecedence.VAR_NAME


class FailedMathExpression(MathExpression):

    def get_str(self, with_spaces: bool = True):
        return "[exception during repr]"

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.PARENTHESIS


@dataclass
class ParenthesisMathExpression(MathExpression):
    expr: MathExpression
    parenthesis_type: Tuple[str, str] = ('(', ')')

    def get_str(self, with_spaces: bool = True):
        return self.parenthesis_type[0] + str(self.expr) + self.parenthesis_type[1]

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.PARENTHESIS


def add_parenthesis_if_needed(expr: MathExpression, needed: bool = False) -> MathExpression:
    return ParenthesisMathExpression(expr) if needed else expr


@dataclass
class ObjectMathExpression(MathExpression):
    obj: Any

    def get_str(self, with_spaces: bool = True):
        return repr(self.obj)

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.VAR_NAME


def object_to_math_expression(obj: Any):
    return obj.get_math_expression() if hasattr(obj, 'get_math_expression') \
        else ObjectMathExpression(obj)
