import copy
import functools
import warnings

from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Any, Dict, Union, Type, Optional, Tuple, Mapping

from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.utilities.iterators import get_object_type_locations_in_args_kwargs
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib


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
    func_definition: Optional[FuncDefinition] = None
    allowed_kwarg_flags: Tuple[str] = ()
    _original_func: Callable = None

    @classmethod
    def from_func(cls, func: Callable, module_or_cls, func_definition=None, *args, **kwargs):
        return cls(func_name=func.__name__, module_or_cls=module_or_cls,
                   func_definition=func_definition, *args, **kwargs)

    def _get_creation_flags(self, args, kwargs):
        """
        Get all the creation flags for creating a quib
        """
        return {}

    def _get_dynamic_flags(self, args, kwargs):
        """
        Get flags found in the quib creation call
        """
        return get_flags_from_kwargs(self.allowed_kwarg_flags, kwargs)

    def _get_func_from_module_or_cls(self):
        return getattr(self.module_or_cls, self.func_name)

    @staticmethod
    def _call_wrapped_func(func, args, kwargs) -> Any:
        return func(*args, **kwargs)

    @staticmethod
    def _modify_kwargs(kwargs):
        return

    def _create_quib_supporting_func(self):
        """
        Create a function which *can* support quibs (and return a quib as a result) if any argument is a quib
        If not, the function will simply run and return it's result
        """

        wrapped_func = self.original_func
        func_definition = self.func_definition

        if hasattr(wrapped_func, '__quibbler_wrapped__'):
            return wrapped_func

        @functools.wraps(wrapped_func)
        def _maybe_create_quib(*args, **kwargs):

            quib_locations = get_object_type_locations_in_args_kwargs(Quib, args, kwargs)

            if quib_locations:
                self._modify_kwargs(kwargs)
                flags = {**self._get_creation_flags(args, kwargs), **self._get_dynamic_flags(args, kwargs)}
                if flags:
                    func_definition_for_quib = copy.deepcopy(func_definition)
                    for key, value in flags.items():
                        setattr(func_definition_for_quib, key, value)
                else:
                    func_definition_for_quib = func_definition

                return create_quib(
                    func=wrapped_func,
                    args=args,
                    kwargs=kwargs,
                    func_definition=func_definition_for_quib,
                    quib_locations=quib_locations,
                )

            return self._call_wrapped_func(wrapped_func, args, kwargs)

        # _maybe_create_quib.func_definition = func_definition
        _maybe_create_quib.__quibbler_wrapped__ = wrapped_func
        _maybe_create_quib.__qualname__ = getattr(wrapped_func, '__name__', str(wrapped_func))

        # TODO: obviously not good solution, how do we fix issue with `np.sum` referring to `np.add`'s attrs?
        # copy all public attr. this takes care of np.ufuncs like np.add.reduce, np.add.outer, etc
        # note that functools.wraps does not take care of attributes in dir but not in __dict__
        # see issue: #345

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # to avoid some "attribute was deprecated" warnings
            for attr in dir(wrapped_func):
                if not attr.startswith('_'):
                    setattr(_maybe_create_quib, attr, getattr(wrapped_func, attr))

        return _maybe_create_quib

    @property
    def original_func(self):
        if self._original_func is None:
            # not overridden yet
            self._original_func = self._get_func_from_module_or_cls()
        return self._original_func

    def override(self) -> Callable:
        """
        Override the original function and make it quibbler supporting
        """
        maybe_create_quib = self._create_quib_supporting_func()
        setattr(self.module_or_cls, self.func_name, maybe_create_quib)
        return maybe_create_quib


@dataclass
class ClassOverride(FuncOverride):
    """
    Overrides the __new__ method of a class to detect quib arguments at object creation.
    """

    def _get_func_from_module_or_cls(self):
        func = super()._get_func_from_module_or_cls()

        if func is object.__new__:
            def wrapped_func(cls, *args, **kwargs):
                obj = func(cls)
                obj.__init__(*args, **kwargs)
                return obj
        else:
            def wrapped_func(cls, *args, **kwargs):
                obj = func(cls, *args, **kwargs)
                return obj

        return wrapped_func

    # @staticmethod
    # def _call_wrapped_func(func, args, kwargs) -> Any:
    #
    #     cls, *args = args
    #
    #     # Below is a workaround for a known problem related to replacing __new__:
    #     # https://stackoverflow.com/questions/70799600/how-exactly-does-python-find-new-and-choose-its-arguments
    #
    #     if func is object.__new__:
    #         obj = func(cls)
    #     else:
    #         obj = func(cls, *args, **kwargs)
    #
    #     obj.__init__(*args, **kwargs)
    #
    #     return obj

    def override(self) -> Callable:
        super().override()
        self.module_or_cls.__quibbler_wrapped__ = self.original_func
        return self.module_or_cls
