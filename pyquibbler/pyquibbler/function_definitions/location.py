from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyquibbler.function_definitions import PositionalArgument
from pyquibbler.function_definitions.types import Argument, KeywordArgument
from pyquibbler.path import PathComponent, Path, deep_get, deep_assign_data_in_path
from pyquibbler.utilities.general_utils import Args, Kwargs


@dataclass
class SourceLocation(ABC):
    """
    Where within the args kwargs is this source located?
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

    def __hash__(self):
        return id(self)

    @property
    def full_path(self):
        return [PathComponent(self.argument.index), *self.path]

    def find_in_args_kwargs(self, args: Args, kwargs: Kwargs):
        return deep_get(args, self.full_path)

    def set_in_args_kwargs(self, args: Args, kwargs: Kwargs, value):
        new_args = deep_assign_data_in_path(args, self.full_path, value)
        return new_args, kwargs


class KeywordSourceLocation(SourceLocation):

    argument: KeywordArgument

    @property
    def full_path(self):
        return [PathComponent(self.argument.keyword), *self.path]

    def set_in_args_kwargs(self, args: Args, kwargs: Kwargs, value):
        new_kwargs = deep_assign_data_in_path(kwargs, self.full_path, value)
        return args, new_kwargs

    def find_in_args_kwargs(self, args: Args, kwargs: Kwargs):
        return deep_get(kwargs, self.full_path)
