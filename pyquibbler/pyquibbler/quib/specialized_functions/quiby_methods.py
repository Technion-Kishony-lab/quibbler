from dataclasses import dataclass

from pyquibbler.quib.quib import Quib
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.function_overriding.attribute_override import MethodOverride


@dataclass(frozen=True)
class CallObjectMethod:
    method: str
    func_definition: FuncDefinition

    def __call__(self, *args, **kwargs):
        obj, *args = args
        return getattr(obj, self.method)(*args, **kwargs)


@dataclass
class QuibyMethod:
    quib: Quib
    method_override: MethodOverride

    def __call__(self, *args, **kwargs):
        """
        Create a function quib that calls the specified method of self.quib
        """
        from pyquibbler.quib.factory import create_quib
        return create_quib(func=CallObjectMethod(method=self.method_override.attribute,
                                                 func_definition=self.method_override.func_definition),
                           args=(self.quib, *args),
                           kwargs=kwargs,
                           )
