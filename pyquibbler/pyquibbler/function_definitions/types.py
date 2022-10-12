from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Union, List, Iterable, Tuple, Any

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


@dataclass(frozen=True)
class SubArgument:

    argument: Union[KeywordArgument, PositionalArgument]
    sub_index: int  # an index within a function argument which is a tuple of actual data arguments


@dataclass(frozen=True)
class DataArgumentDesignation:

    argument: Union[KeywordArgument, PositionalArgument]
    is_multi_arg: bool = False  # indicates if the argument is a tuple representing multiple data arguments


Argument = Union[KeywordArgument, PositionalArgument, SubArgument]

RawArgument = Union[str, int]


def convert_raw_data_arguments_to_data_argument_designations(
        data_source_arguments: List[Union[RawArgument, DataArgumentDesignation]] = None
                                                            ) -> List[DataArgumentDesignation]:
    data_source_arguments = data_source_arguments or list()

    def _convert(raw_argument):
        if isinstance(raw_argument, DataArgumentDesignation):
            return raw_argument
        argument = PositionalArgument(raw_argument) if isinstance(raw_argument, int) \
            else KeywordArgument(raw_argument)
        return DataArgumentDesignation(argument, is_multi_arg=False)

    return [_convert(data_source_argument) for data_source_argument in data_source_arguments]


def iter_arg_ids_and_values(args: Args, kwargs: Kwargs) -> Iterable[Tuple[ArgId, Any]]:
    return chain(enumerate(args), kwargs.items())
