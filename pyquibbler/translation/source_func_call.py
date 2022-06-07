import dataclasses
from typing import Callable, Tuple, Any, Mapping, TYPE_CHECKING, Optional, List

from pyquibbler.function_definitions import get_definition_for_function, SourceLocation
from pyquibbler.function_definitions.func_call import FuncCall, FuncArgsKwargs
from pyquibbler.translation.types import Source

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


@dataclasses.dataclass
class SourceFuncCall(FuncCall):
    func_definition: 'FuncDefinition' = None
    func_args_kwargs: FuncArgsKwargs = None

    """
    A FuncCall with `Source` objects for any sources in the arguments
    """

    SOURCE_OBJECT_TYPE = Source

    @classmethod
    def from_(cls, func: Callable,
              func_args: Tuple[Any, ...],
              func_kwargs: Mapping[str, Any],
              include_defaults: bool = False,
              func_definition: 'FuncDefinition' = None,
              quib_locations: Optional[List[SourceLocation]] = None,
              *args, **kwargs):
        func_definition = func_definition or get_definition_for_function(func)
        if quib_locations is None:
            from pyquibbler.quib.utils.iterators import get_source_locations_in_args_kwargs
            quib_locations = get_source_locations_in_args_kwargs(func_args, func_kwargs)
        return cls(func_args_kwargs=FuncArgsKwargs(func, func_args, func_kwargs, include_defaults),
                   func_definition=func_definition,
                   quib_locations=quib_locations,
                   *args, **kwargs)

    def run(self):
        """
        Calls a function with the specified args and kwargs while replacing quibs with their values.
        """

        def _replace_source_with_value(source: Source):
            return source.value

        new_args, new_kwargs = self.transform_sources_in_args_kwargs(_replace_source_with_value,
                                                                     _replace_source_with_value)
        return self.func(*new_args, **new_kwargs)

    def __hash__(self):
        return id(self)
