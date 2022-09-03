from dataclasses import dataclass
from typing import Callable, Tuple, Any, Dict

from .math_expression import MathExpression
from ..math_precedence import MathPrecedence


@dataclass
class FunctionCallMathExpression(MathExpression):
    func_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def get_pretty_args(self):
        return [repr(arg) for arg in self.args]

    def get_pretty_kwargs(self):
        return [f'{key}={repr(val)}' for key, val in self.kwargs.items()]

    def get_str(self, with_spaces: bool = True):
        return f'{self.func_name}({", ".join([*self.get_pretty_args(), *self.get_pretty_kwargs()])})'

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.FUNCTION_CALL


def vectorize_call_converter(func: Callable,
                             args: Tuple[Any, ...],
                             kwargs: Dict[str, Any]) -> FunctionCallMathExpression:
    func_being_called, *args = args
    return FunctionCallMathExpression(str(func_being_called), args, kwargs)


def function_call_converter(func: Callable,
                            args: Tuple[Any, ...],
                            kwargs: Dict[str, Any]) -> FunctionCallMathExpression:
    func_name = getattr(func, '__name__', str(func))
    return FunctionCallMathExpression(func_name, args, kwargs)


def str_format_call_converter(func: Callable,
                              args: Tuple[Any, ...],
                              kwargs: Dict[str, Any]) -> FunctionCallMathExpression:
    func_name = getattr(func, '__name__', str(func))
    str_ = getattr(func, '__reduce__')()[1][0]
    str_format_name = f'"{str_}".{func_name}'
    return FunctionCallMathExpression(str_format_name, args, kwargs)


def is_str_format(func: Callable) -> bool:
    return getattr(func, '__qualname__', None) == 'str.format'
