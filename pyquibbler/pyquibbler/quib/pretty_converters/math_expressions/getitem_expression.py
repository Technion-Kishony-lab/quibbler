from dataclasses import dataclass
from typing import Callable, Any

from pyquibbler.utilities.general_utils import Args
from .math_expression import MathExpression
from ..math_precedence import MathPrecedence


def _convert_sub_item(sub_item: Any) -> str:
    if isinstance(sub_item, slice):
        return _convert_slice(sub_item)
    if isinstance(sub_item, type(Ellipsis)):
        return '...'
    return repr(sub_item)


def _convert_slice(slice_: slice) -> str:
    pretty = ':'
    if slice_.start is not None:
        pretty = f"{slice_.start}{pretty}"
    if slice_.stop is not None:
        pretty = f"{pretty}{slice_.stop}"
    if slice_.step is not None:
        pretty = f"{pretty}:{slice_.step}"
    return pretty


@dataclass
class GetItemExpression(MathExpression):
    obj: Any
    item: Any

    def get_str(self, with_spaces: bool = True):
        if isinstance(self.item, tuple):
            item_repr = ", ".join(_convert_sub_item(sub_item) for sub_item in self.item)
            if len(self.item) == 1:
                item_repr = f"({item_repr},)"
        else:
            item_repr = _convert_sub_item(self.item)
        return f"{self.obj}[{item_repr}]"

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.SUBSCRIPTION


def getitem_converter(func: Callable, args: Args) -> GetItemExpression:
    obj, item = args
    return GetItemExpression(obj, item)
