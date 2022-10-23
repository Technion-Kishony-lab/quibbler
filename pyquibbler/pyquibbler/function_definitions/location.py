from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from pyquibbler.path import PathComponent, Path, deep_get, deep_set
from pyquibbler.utilities.general_utils import Args, Kwargs
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type

from .types import Argument, KeywordArgument, PositionalArgument, SubArgument


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

    def get_path_in_argument(self, argument: Argument):
        """
        Returns None if not in argument, or otherwise the path in the argument
        """
        if self.argument == argument:
            return self.path
        if isinstance(argument, SubArgument) \
                and self.argument == argument.argument and self.path[0].component == argument.sub_index:
            return self.path[1:]
        return None


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
        new_args = deep_set(args, self.full_path, value)
        return new_args, kwargs


class KeywordSourceLocation(SourceLocation):

    argument: KeywordArgument

    @property
    def full_path(self):
        return [PathComponent(self.argument.keyword), *self.path]

    def set_in_args_kwargs(self, args: Args, kwargs: Kwargs, value):
        new_kwargs = deep_set(kwargs, self.full_path, value)
        return args, new_kwargs

    def find_in_args_kwargs(self, args: Args, kwargs: Kwargs):
        return deep_get(kwargs, self.full_path)


def get_object_type_locations_in_args_kwargs(object_type, args: Args, kwargs: Kwargs) -> List[SourceLocation]:
    """
    Find all objects of a given type in args and kwargs and return their locations
    """
    positional_locations = [PositionalSourceLocation(PositionalArgument(path[0].component), path[1:]) for
                            path in get_paths_for_objects_of_type(args, object_type)]
    keyword_locations = [KeywordSourceLocation(KeywordArgument(path[0].component), path[1:]) for
                         path in get_paths_for_objects_of_type(kwargs, object_type)]
    return positional_locations + keyword_locations
