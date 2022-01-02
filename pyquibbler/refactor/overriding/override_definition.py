import functools
from dataclasses import dataclass, field
from types import ModuleType

from typing import Callable, Any, Dict, Union, Type, Optional, Set, List

from pyquibbler.env import EVALUATE_NOW
from pyquibbler.refactor.quib.function_runners import FunctionRunner, DefaultFunctionRunner
from pyquibbler.refactor.inversion.inverter import Inverter
from pyquibbler.refactor.quib.utils import is_there_a_quib_in_args
from pyquibbler.refactor.overriding.types import Argument, IndexArgument, KeywordArgument

from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator


# TODO: Docs!
@dataclass
class OverrideDefinition:
    func_name: str
    module_or_cls: Union[ModuleType, Type]
    quib_creation_flags: Optional[Dict[str, Any]] = None
    data_source_arguments: Set[Argument] = field(default_factory=set)
    inverters: List[Type[Inverter]] = None
    backwards_path_translators: List[Type[BackwardsPathTranslator]] = field(default_factory=list)
    forwards_path_translators: List[Type[ForwardsPathTranslator]] = field(default_factory=list)
    function_runner_cls: Type[FunctionRunner] = DefaultFunctionRunner

    _original_func: Callable = None

    @classmethod
    def from_func(cls, func: Callable, data_source_arguments: Set[Union[int, str]] = None, *args, **kwargs):
        data_source_arguments = data_source_arguments or set()
        raw_data_source_arguments = {
            IndexArgument(data_source_argument)
            if isinstance(data_source_argument, int)
            else KeywordArgument(data_source_argument)
            for data_source_argument in data_source_arguments
        }
        return cls(func_name=func.__name__, data_source_arguments=raw_data_source_arguments, *args, **kwargs)

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return {}

    @property
    def _flags(self):
        return {
            **self._default_creation_flags,
            **(self.quib_creation_flags or {})
        }

    def _get_func_from_module_or_cls(self):
        return getattr(self.module_or_cls, self.func_name)

    def _create_quib_supporting_func(self):
        wrapped_func = self._get_func_from_module_or_cls()

        @functools.wraps(wrapped_func)
        def _maybe_create_quib(*args, **kwargs):
            from pyquibbler.refactor.quib.factory import create_quib
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._flags
                evaluate_now = flags.pop('evaluate_now', EVALUATE_NOW)
                return create_quib(
                    func=wrapped_func,
                    args=args,
                    kwargs=kwargs,
                    evaluate_now=evaluate_now,
                    **flags
                )
            return wrapped_func(*args, **kwargs)

        _maybe_create_quib.__quibbler_wrapped__ = wrapped_func
        return _maybe_create_quib

    @property
    def original_func(self):
        if self._original_func is None:
            # not overridden yet
            return self._get_func_from_module_or_cls()
        return self._original_func

    def override(self):
        self._original_func = self._get_func_from_module_or_cls()
        setattr(self.module_or_cls, self.func_name, self._create_quib_supporting_func())
