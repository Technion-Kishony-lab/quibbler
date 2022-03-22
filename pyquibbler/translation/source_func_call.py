import dataclasses
from typing import Callable, Tuple, Any, Mapping

from pyquibbler.function_definitions.func_call import FuncCall, FuncArgsKwargs
from pyquibbler.translation.types import Source


@dataclasses.dataclass
class SourceFuncCall(FuncCall):
    args_values: FuncArgsKwargs = None

    """
    A funccall with `Source` objects for any sources in the arguments
    """

    SOURCE_OBJECT_TYPE = Source

    @classmethod
    def from_(cls, func: Callable,
              func_args: Tuple[Any, ...],
              func_kwargs: Mapping[str, Any],
              include_defaults: bool = False,
              *args, **kwargs):
        return cls(args_values=FuncArgsKwargs(func, func_args, func_kwargs, include_defaults),
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
