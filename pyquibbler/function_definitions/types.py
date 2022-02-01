from dataclasses import dataclass
from typing import Union, List, Set


@dataclass(frozen=True)
class PositionalArgument:

    index: int


@dataclass(frozen=True)
class KeywordArgument:

    keyword: str


Argument = Union[KeywordArgument, PositionalArgument]

RawArgument = Union[str, int]


def convert_raw_data_source_argument_to_data_source_argument(
        data_source_arguments: List[RawArgument] = None) -> Set[Argument]:
    data_source_arguments = data_source_arguments or set()
    return {
        PositionalArgument(data_source_argument)
        if isinstance(data_source_argument, int)
        else KeywordArgument(data_source_argument)
        for data_source_argument in data_source_arguments
    }


