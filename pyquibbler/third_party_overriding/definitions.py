import functools
from dataclasses import dataclass
from types import ModuleType

from typing import Callable, Any, Dict, Union, Type, Optional

from pyquibbler.env import EVALUATE_NOW
from pyquibbler.quib.function_quibs.utils import ArgsValues
from pyquibbler.quib.refactor.factory import create_quib
from pyquibbler.quib.refactor.utils import is_there_a_quib_in_args


@dataclass
class OverrideDefinition:
    func_name: str
    module_or_cls: Union[ModuleType, Type]
    quib_creation_flags: Optional[Dict[str, Any]] = None

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

    def override(self):
        previous_func = getattr(self.module_or_cls, self.func_name)

        @functools.wraps(previous_func)
        def _create_quib(*args, **kwargs):
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._flags
                evaluate_now = flags.pop('evaluate_now', EVALUATE_NOW)
                args_values = ArgsValues.from_function_call(func=previous_func,
                                                            args=args,
                                                            kwargs=kwargs,
                                                            include_defaults=False)
                return create_quib(
                    func=functools.partial(self._run_previous_func, previous_func, args_values),
                    args=args,
                    kwargs=kwargs,
                    evaluate_now=evaluate_now,
                    **flags
                )
            return previous_func(*args, **kwargs)

        setattr(self.module_or_cls, self.func_name, _create_quib)
