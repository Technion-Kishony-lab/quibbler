from dataclasses import dataclass
from typing import Callable, Tuple, Any, Dict

from pyquibbler.user_utils.is_quiby import is_quib
from pyquibbler.user_utils.quiby_methods import is_property
from pyquibbler.utilities.general_utils import Args, Kwargs
from pyquibbler.utilities.iterators import is_user_object
from .math_expression import MathExpression
from ..math_precedence import MathPrecedence


def _get_public_attrs_for_class(cls):
    """Return a list of public attributes of a class (not starting with '_ and not callable)"""
    return [attr for attr in dir(cls) if not attr.startswith('_') and not callable(getattr(cls, attr))]

def _get_public_attrs_for_instance(obj):
    """Return a list of public attributes of an object (not starting with '_ and not callable)"""
    attrnames = []
    for attrname in dir(obj):
        if attrname.startswith('_'):
            continue
        attr = getattr(obj, attrname)
        if callable(attr):
            continue
        if is_property(type(obj), attrname):
            continue
        # avoid class attributes:
        if hasattr(obj.__class__, attrname) and getattr(obj.__class__, attrname) == getattr(obj, attrname):
            continue
        attrnames.append(attrname)

    return attrnames


def _get_public_attrs(obj):
    if hasattr(obj, '__dict__'):
        return _get_public_attrs_for_instance(obj)
    else:
        return _get_public_attrs_for_class(obj.__class__)


def _arg_repr(obj):
    # convert something like  <tests.test_attr_quibs.quiby_class.<locals>.Obj object at 0x10c7acf90>
    # to something like Obj
    if not is_user_object(obj):
        return repr(obj)
    if is_quib(obj):
        return repr(obj)
    cls_name = type(obj).__name__
    public_attrs = _get_public_attrs(obj)
    return f'{cls_name}({", ".join(f"{attr}={getattr(obj, attr)!r}" for attr in public_attrs)})'


@dataclass
class FunctionCallMathExpression(MathExpression):
    func_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def get_pretty_args(self):
        return [_arg_repr(arg) for arg in self.args]

    def get_pretty_kwargs(self):
        return [f'{key}={_arg_repr(val)}' for key, val in self.kwargs.items()]

    def get_str(self, with_spaces: bool = True):
        return f'{self.func_name}({", ".join([*self.get_pretty_args(), *self.get_pretty_kwargs()])})'

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.FUNCTION_CALL


def vectorize_call_converter(func: Callable, args: Args, kwargs: Kwargs) -> FunctionCallMathExpression:
    func_being_called, *args = args
    return FunctionCallMathExpression(str(func_being_called), args, kwargs)


def function_call_converter(func: Callable, args: Args, kwargs: Kwargs) -> FunctionCallMathExpression:
    func_name = getattr(func, '__name__', str(func))
    return FunctionCallMathExpression(func_name, args, kwargs)


def str_format_call_converter(func: Callable, args: Args, kwargs: Kwargs) -> FunctionCallMathExpression:
    func_name = getattr(func, '__name__', str(func))
    str_ = getattr(func, '__reduce__')()[1][0]
    str_format_name = f'"{str_}".{func_name}'
    return FunctionCallMathExpression(str_format_name, args, kwargs)


def is_str_format(func: Callable) -> bool:
    return getattr(func, '__qualname__', None) == 'str.format'
