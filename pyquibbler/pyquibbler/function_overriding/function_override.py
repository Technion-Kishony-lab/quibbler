import copy
import functools
import warnings

from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Any, Dict, Union, Type, Optional, Tuple, Mapping, List

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.function_definitions.location import get_object_type_locations_in_args_kwargs, SourceLocation
from pyquibbler.quib.get_value_context_manager import get_value_context_pass_quibs
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib
from pyquibbler.utilities.general_utils import Args, Kwargs


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
    should_remove_arguments_equal_to_defaults: bool = False
    _original_func: Callable = None

    def _get_creation_flags(self, args: Args, kwargs: Kwargs):
        """
        Get all the creation flags for creating a quib
        """
        return {}

    def _get_dynamic_flags(self, args: Args, kwargs: Kwargs):
        """
        Get flags found in the quib creation call
        """
        return get_flags_from_kwargs(self.allowed_kwarg_flags, kwargs)

    def _get_func_from_module_or_cls(self):
        return getattr(self.module_or_cls, self.func_name)

    @staticmethod
    def _call_wrapped_func(func, args: Args, kwargs: Kwargs) -> Any:
        return func(*args, **kwargs)

    @staticmethod
    def _modify_args_kwargs(args: Args, kwargs: Kwargs, quib_locations: List[SourceLocation]
                            ) -> Tuple[Args, Kwargs, Optional[List[SourceLocation]]]:
        return args, kwargs, quib_locations

    @staticmethod
    def should_create_quib(func, args, kwargs):
        return True

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

            if get_value_context_pass_quibs() is not False:
                quib_locations = get_object_type_locations_in_args_kwargs(Quib, args, kwargs)

                if quib_locations and self.should_create_quib(wrapped_func, args, kwargs):
                    args, kwargs, quib_locations = self._modify_args_kwargs(args, kwargs, quib_locations)
                    flags = {**self._get_creation_flags(args, kwargs), **self._get_dynamic_flags(args, kwargs)}
                    if self.should_remove_arguments_equal_to_defaults:
                        kwargs = FuncArgsKwargs(wrapped_func, args, kwargs).get_kwargs_without_those_equal_to_defaults()

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

        @functools.wraps(func)
        def wrapped_new(cls, *args, should_call_init=True, **kwargs):

            # A workaround for a known issue related to overloading __new__
            # https://stackoverflow.com/questions/70799600/how-exactly-does-python-find-new-and-choose-its-arguments
            obj = func(cls) if func is object.__new__ else func(cls, *args, **kwargs)

            if should_call_init:
                obj.__init__(*args, **kwargs)

            return obj

        wrapped_new.wrapped__new__ = True

        return wrapped_new

    @staticmethod
    def _call_wrapped_func(func, args, kwargs) -> Any:
        return func(should_call_init=False, *args, **kwargs)

    def override(self) -> Callable:
        super().override()
        self.module_or_cls.__quibbler_wrapped__ = self.original_func
        return self.module_or_cls


@dataclass
class NotImplementedFunc(PyQuibblerException):
    func: Callable = None
    message: str = ''

    def __str__(self):
        return f'Function {self.func.__qualname__} is not implemented to work with quibs. \n{self.message}\n'


@dataclass
class NotImplementedOverride(FuncOverride):
    """
    Overrides the function to issue an exception if called with quib arguments.
    """

    message: str = ''

    def _create_quib_supporting_func(self):

        wrapped_func = self.original_func

        @functools.wraps(wrapped_func)
        def _issue_exception_when_apply_to_quibs(*args, **kwargs):

            quib_locations = get_object_type_locations_in_args_kwargs(Quib, args, kwargs)

            if quib_locations:
                raise NotImplementedFunc(wrapped_func, self.message) from None

            return wrapped_func(*args, **kwargs)

        return _issue_exception_when_apply_to_quibs
