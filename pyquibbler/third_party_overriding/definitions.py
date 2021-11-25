import functools
from dataclasses import dataclass
from types import ModuleType

from typing import Callable, Any, Dict, Union, Type, Optional

from pyquibbler.quib.refactor.factory import create_quib


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
            return create_quib(
                func=previous_func,
                args=args,
                kwargs=kwargs,
                **self._flags
            )

        setattr(self.module_or_cls, self.func_name, _create_quib)
