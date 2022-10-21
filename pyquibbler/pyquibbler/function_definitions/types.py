from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import chain
from typing import Union, List, Iterable, Tuple, Any

from pyquibbler.utilities.general_utils import Args, Kwargs


ArgId = Union[int, str]


class Argument(ABC):

    @abstractmethod
    def get_arg_id(self):
        pass


@dataclass(frozen=True)
class PositionalArgument(Argument):

    index: int

    def get_arg_id(self):
        return self.index


@dataclass(frozen=True)
class KeywordArgument(Argument):

    keyword: str

    def get_arg_id(self):
        return self.keyword


@dataclass(frozen=True)
class SubArgument(Argument):

    argument: Union[KeywordArgument, PositionalArgument]
    sub_index: int  # an index within a function argument which is a tuple of actual data arguments

    def get_arg_id(self):
        assert False


@dataclass(frozen=True)
class DataArgumentDesignation:

    argument: Union[KeywordArgument, PositionalArgument]
    is_multi_arg: bool = False  # indicates if the argument is a tuple representing multiple data arguments


def convert_argument_id_to_argument(argument_id: ArgId) -> Union[PositionalArgument, KeywordArgument]:
    return PositionalArgument(argument_id) if isinstance(argument_id, int) \
        else KeywordArgument(argument_id)


def convert_raw_data_arguments_to_data_argument_designations(
        data_source_arguments: List[Union[ArgId, DataArgumentDesignation]] = None
                                                            ) -> List[DataArgumentDesignation]:
    data_source_arguments = data_source_arguments or list()

    def _convert(raw_argument):
        if isinstance(raw_argument, DataArgumentDesignation):
            return raw_argument
        return DataArgumentDesignation(convert_argument_id_to_argument(raw_argument), is_multi_arg=False)

    return [_convert(data_source_argument) for data_source_argument in data_source_arguments]


def iter_arg_ids_and_values(args: Args, kwargs: Kwargs) -> Iterable[Tuple[ArgId, Any]]:
    return chain(enumerate(args), kwargs.items())
