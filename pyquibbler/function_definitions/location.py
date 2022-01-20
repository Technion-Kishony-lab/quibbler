from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyquibbler.function_definitions import PositionalArgument
from pyquibbler.function_definitions.types import Argument, KeywordArgument
from pyquibbler.path import PathComponent, Path, deep_get, deep_assign_data_in_path
from pyquibbler.utilities.general_utils import Args, Kwargs


@dataclass
class SourceLocation(ABC):
    """
    Where within the args kwargs in this source located?
    """
    argument: Argument
    path: Path

    @abstractmethod
    def find_in_args_kwargs(self, args: Args, kwargs: Kwargs):
        """
        Given args and kwargs, get the value referenced by the location's argument and path
        """
        pass

    @abstractmethod
    def set_in_args_kwargs(self, args: Args, kwargs: Kwargs, value):
        """
        Given args and kwargs, set to the value referenced by the location's argument and path
        """
        pass


class PositionalSourceLocation(SourceLocation):

    argument: PositionalArgument

    @property
    def full_path(self):
        return [PathComponent(component=self.argument.index, indexed_cls=tuple), *self.path]

    def find_in_args_kwargs(self, args: Args, kwargs: Kwargs):
        return deep_get(args, self.full_path)

    def set_in_args_kwargs(self, args: Args, kwargs: Kwargs, value):
        new_args = deep_assign_data_in_path(args, self.full_path, value)
        return new_args, kwargs


class KeywordSourceLocation(SourceLocation):

    argument: KeywordArgument

    @property
    def full_path(self):
        return [PathComponent(component=self.argument.keyword, indexed_cls=dict), *self.path]

    def set_in_args_kwargs(self, args: Args, kwargs: Kwargs, value):
        new_kwargs = deep_assign_data_in_path(kwargs, self.full_path, value)
        return args, new_kwargs

    def find_in_args_kwargs(self, args: Args, kwargs: Kwargs):
        return deep_get(kwargs, self.full_path)


def create_source_location(argument: Argument, path: Path) -> SourceLocation:
    """
    Create a location of a source- this location indicates where the source is within the args kwargs,
    and provides helper utilities to get and set values to the source's location within the args kwargs
    """
    if isinstance(argument, PositionalArgument):
        return PositionalSourceLocation(argument, path)
    else:
        return KeywordSourceLocation(argument, path)
