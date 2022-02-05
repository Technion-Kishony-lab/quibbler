import functools
from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Any, Dict, Union, Type, Optional

from pyquibbler.env import EVALUATE_NOW, REVEAL_THIRD_PARTY_CALLS
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.quib.utils.miscellaneous import is_there_a_quib_in_args


@dataclass
class FuncOverride:
    """
    Represents an override of a function, a "replacement" of it in order to support Quibs.
    The default implementation is to be completely transparent if no quibs are given as arguments.
    """

    module_or_cls: Union[ModuleType, Type]
    func_name: str
    function_definition: Optional[FuncDefinition] = None
    quib_creation_flags: Optional[Dict[str, Any]] = None
    _original_func: Callable = None

    @classmethod
    def from_func(cls, func: Callable, module_or_cls, function_definition=None, *args, **kwargs):
        return cls(func_name=func.__name__, module_or_cls=module_or_cls,
                   function_definition=function_definition, *args, **kwargs)

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        """
        What are the default flags for creating a Quib for this FuncOverride?
        If you subclass this, you can override this, the default is to use the default flags
        """
        return {}

    def _get_creation_flags(self, args, kwargs):
        """
        Get all the creation flags for creating a quib
        """
        return {
            **self._default_creation_flags,
            **(self.quib_creation_flags or {})
        }

    def _get_func_from_module_or_cls(self):
        return getattr(self.module_or_cls, self.func_name)

    def _create_quib_supporting_func(self):
        """
        Create a function which *can* support quibs (and return a quib as a result) if any argument is a quib
        If not, the function will simply run and return it's result
        """

        wrapped_func = self.original_func

        @functools.wraps(wrapped_func)
        def call_third_party(*args, **kwargs):
            print('Quibbler calls: ', wrapped_func)
            return wrapped_func(*args, **kwargs)

        call_third_party.__quibbler_third_party_called__ = wrapped_func

        @functools.wraps(wrapped_func)
        def _maybe_create_quib(*args, **kwargs):
            from pyquibbler.quib.factory import create_quib
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._get_creation_flags(args, kwargs)
                evaluate_now = flags.pop('evaluate_now', EVALUATE_NOW)
                return create_quib(
                    func=call_third_party if REVEAL_THIRD_PARTY_CALLS else wrapped_func,
                    args=args,
                    kwargs=kwargs,
                    evaluate_now=evaluate_now,
                    **flags
                )
            return wrapped_func(*args, **kwargs)

        _maybe_create_quib.__quibbler_wrapped__ = wrapped_func

        # TODO: obviously not good solution, how do we fix issue with `np.sum` referring to `np.add`'s attrs?
        if hasattr(wrapped_func, 'reduce'):
            _maybe_create_quib.reduce = wrapped_func.reduce

        return _maybe_create_quib

    @property
    def original_func(self):
        if self._original_func is None:
            # not overridden yet
            return self._get_func_from_module_or_cls()
        return self._original_func

    def override(self):
        """
        Override the original function and make it quibbler supporting
        """
        self._original_func = self._get_func_from_module_or_cls()
        setattr(self.module_or_cls, self.func_name, self._create_quib_supporting_func())
