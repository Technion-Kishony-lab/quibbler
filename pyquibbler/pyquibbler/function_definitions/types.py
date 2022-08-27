from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Union, List, Set, Iterable, Tuple, Any

from pyquibbler.utilities.general_utils import Args, Kwargs

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.func_calling.func_calls.vectorize.vectorize_metadata import ArgId


@dataclass(frozen=True)
class PositionalArgument:

    index: int


@dataclass(frozen=True)
class KeywordArgument:

    keyword: str


Argument = Union[KeywordArgument, PositionalArgument]

RawArgument = Union[str, int]


def convert_raw_data_source_arguments_to_data_source_arguments(
        data_source_arguments: List[RawArgument] = None) -> Set[Argument]:
    data_source_arguments = data_source_arguments or set()
    return {
        PositionalArgument(data_source_argument)
        if isinstance(data_source_argument, int)
        else KeywordArgument(data_source_argument)
        for data_source_argument in data_source_arguments
    }


def iter_arg_ids_and_values(args: Args, kwargs: Kwargs) -> Iterable[Tuple[ArgId, Any]]:
    return chain(enumerate(args), kwargs.items())
