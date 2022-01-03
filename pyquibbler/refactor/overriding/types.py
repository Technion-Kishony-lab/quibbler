from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class PositionalArgument:

    index: int


@dataclass(frozen=True)
class KeywordArgument:

    keyword: str


Argument = Union[KeywordArgument, PositionalArgument]
