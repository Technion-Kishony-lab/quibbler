from dataclasses import dataclass
from typing import Callable, Any

from pyquibbler.utilities.general_utils import Args
from .math_expression import MathExpression
from ..math_precedence import MathPrecedence


@dataclass
class GetAttrExpression(MathExpression):
    obj: Any
    item: str

    def get_str(self, with_spaces: bool = True):
        return f"{self.obj}.{self.item}"

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.SUBSCRIPTION


def getattr_converter(func: Callable, args: Args) -> GetAttrExpression:
    obj, item = args
    return GetAttrExpression(obj, item)
