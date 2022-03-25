import copy
import functools
from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Any, Dict, Union, Type, Optional, Tuple, Mapping

from pyquibbler.env import EVALUATE_NOW
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.quib.utils.miscellaneous import is_there_a_quib_in_args


def get_flags_from_kwargs(flag_names: Tuple[str, ...], kwargs: Dict[str, Any]) -> Mapping[str, Any]:
    return {key: kwargs.pop(key) for key in flag_names if key in kwargs.keys()}


@dataclass
class FuncOverride:
    """
    Represents an override of a function, a "replacement" of it in order to support Quibs.
    The default implementation is to be completely transparent if no quibs are given as arguments.
    """

    module_or_cls: Union[ModuleType, Type]
    func_name: str
    function_definition: Optional[FuncDefinition] = None
    _original_func: Callable = None

    @classmethod
    def from_func(cls, func: Callable, module_or_cls, function_definition=None, *args, **kwargs):
        return cls(func_name=func.__name__, module_or_cls=module_or_cls,
                   function_definition=function_definition, *args, **kwargs)

    def _get_creation_flags(self, args, kwargs):
        """
        Get all the creation flags for creating a quib
        """
        return {}

    def _get_func_from_module_or_cls(self):
        return getattr(self.module_or_cls, self.func_name)

    @staticmethod
    def _call_wrapped_func(func, args, kwargs) -> Any:
        return func(*args, **kwargs)

    def _create_quib_supporting_func(self):
        """
        Create a function which *can* support quibs (and return a quib as a result) if any argument is a quib
        If not, the function will simply run and return it's result
        """

        wrapped_func = self.original_func
        function_definition = self.function_definition

        @functools.wraps(wrapped_func)
        def _maybe_create_quib(*args, **kwargs):
            from pyquibbler.quib.factory import create_quib
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._get_creation_flags(args, kwargs)
                dynamic_flags = get_flags_from_kwargs(('call_func_with_quibs', 'evaluate_now'), kwargs)
                all_flags = {**flags, **dynamic_flags}
                if all_flags:
                    func_definition_for_quib = copy.deepcopy(function_definition)
                    for key, value in all_flags.items():
                        setattr(func_definition_for_quib, key, value)
                else:
                    func_definition_for_quib = function_definition

                return create_quib(
                    func=wrapped_func,
                    args=args,
                    kwargs=kwargs,
                    function_definition=func_definition_for_quib,
                )

            return self._call_wrapped_func(wrapped_func, args, kwargs)

        # _maybe_create_quib.function_definition = function_definition
        _maybe_create_quib.__quibbler_wrapped__ = wrapped_func
        _maybe_create_quib.__qualname__ = getattr(wrapped_func, '__name__', str(wrapped_func))

        # TODO: obviously not good solution, how do we fix issue with `np.sum` referring to `np.add`'s attrs?
        # copy all public attr. this takes care of np.ufuncs like np.add.reduce, np.add.outer, etc
        # note that functools.wraps does not take care of attributes in dir but not in __dict__
        # see issue: #345
        for attr in dir(wrapped_func):
            if not attr.startswith('_'):
                setattr(_maybe_create_quib, attr, getattr(wrapped_func, attr))

        return _maybe_create_quib

    @property
    def original_func(self):
        if self._original_func is None:
            # not overridden yet
            return self._get_func_from_module_or_cls()
        return self._original_func

    def override(self) -> Callable:
        """
        Override the original function and make it quibbler supporting
        """
        self._original_func = self._get_func_from_module_or_cls()
        maybe_create_quib = self._create_quib_supporting_func()
        setattr(self.module_or_cls, self.func_name, maybe_create_quib)
        return maybe_create_quib
