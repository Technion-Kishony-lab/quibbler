import functools
from dataclasses import dataclass
from types import ModuleType

from typing import Callable, Any, Dict, Union, Type, Optional

from pyquibbler.env import EVALUATE_NOW
from pyquibbler.quib.refactor.factory import create_quib
from pyquibbler.quib.refactor.utils import is_there_a_quib_in_args


@dataclass
class OverrideDefinition:
    module_or_cls: Union[ModuleType, Type]
    func_name: str
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

    def override(self):
        previous_func = getattr(self.module_or_cls, self.func_name)

        @functools.wraps(previous_func)
        def _create_quib(*args, **kwargs):
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._flags
                evaluate_now = flags.pop('evaluate_now', EVALUATE_NOW)
                return create_quib(
                    func=previous_func,
                    args=args,
                    kwargs=kwargs,
                    evaluate_now=evaluate_now,
                    **flags
                )
            return previous_func(*args, **kwargs)

        setattr(self.module_or_cls, self.func_name, _create_quib)
