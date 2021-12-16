import functools
import inspect
from dataclasses import dataclass, field
from types import ModuleType

from typing import Callable, Any, Dict, Union, Type, Optional, Set

from pyquibbler.env import EVALUATE_NOW
from pyquibbler.quib.function_quibs.utils import ArgsValues
from pyquibbler.quib.refactor.utils import is_there_a_quib_in_args
from pyquibbler.overriding.types import Argument, IndexArgument, KeywordArgument

# TODO: Docs!


@dataclass
class OverrideDefinition:
    func_name: str
    module_or_cls: Union[ModuleType, Type]
    quib_creation_flags: Optional[Dict[str, Any]] = None
    data_source_arguments: Set[Argument] = field(default_factory=set)

    @classmethod
    def from_func(cls, func: Callable, data_source_arguments: Set[Union[int, str]] = None, *args, **kwargs):
        data_source_arguments = data_source_arguments or set()
        raw_data_source_arguments = {
            IndexArgument(data_source_argument)
            if isinstance(data_source_argument, int)
            else KeywordArgument(data_source_argument)
            for data_source_argument in data_source_arguments
        }
        return cls(func_name=func.__name__, data_source_arguments=raw_data_source_arguments, **kwargs)

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return {}

    @property
    def _flags(self):
        return {
            **self._default_creation_flags,
            **(self.quib_creation_flags or {})
        }

    def _run_previous_func(self, previous_func: Callable, args_values, *args, **kwargs):
        return previous_func(*args, **kwargs)

    def _get_wrapped_func(self):
        return getattr(self.module_or_cls, self.func_name)

    def _create_func_to_maybe_create_quib(self, wrapped_func: Callable):
        @functools.wraps(wrapped_func)
        def _maybe_create_quib(*args, **kwargs):
            from pyquibbler.quib.refactor.factory import create_quib
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._flags
                evaluate_now = flags.pop('evaluate_now', EVALUATE_NOW)
                args_values = ArgsValues.from_function_call(func=wrapped_func,
                                                            args=args,
                                                            kwargs=kwargs,
                                                            include_defaults=False)
                partial_wrapped_func = functools.partial(self._run_previous_func, wrapped_func, args_values)
                partial_wrapped_func.func_to_invert = wrapped_func
                return create_quib(
                    func=partial_wrapped_func,
                    args=args,
                    kwargs=kwargs,
                    evaluate_now=evaluate_now,
                    **flags
                )
            return wrapped_func(*args, **kwargs)

        return _maybe_create_quib

    def override(self):
        setattr(self.module_or_cls, self.func_name, self._create_func_to_maybe_create_quib(self._get_wrapped_func()))
