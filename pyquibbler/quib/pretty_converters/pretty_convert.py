import operator
from typing import Callable, List, Union
from typing import Tuple, Any, Mapping

import numpy as np

from pyquibbler.utilities.iterators import recursively_run_func_on_object
from pyquibbler.quib.pretty_converters.convert_math_equations import MATH_FUNCS_TO_CONVERTERS, \
    MathExpression


def _convert_slice(slice_: slice):
    pretty = ':'
    if slice_.start is not None:
        pretty = f"{slice_.start}{pretty}"
    if slice_.stop is not None:
        pretty = f"{pretty}{slice_.stop}"
    if slice_.step is not None:
        pretty = f"{pretty}:{slice_.step}"
    return pretty


def _convert_iterable(itr):
    iterable_rep = repr(type(itr)())
    return f"{iterable_rep[0]}{', '.join(itr)}{iterable_rep[1]}"


ITEMS_TO_CONVERTERS = {
    slice: _convert_slice,
    type(...): lambda *_: '...',
    type(None): lambda *_: None
}


def replace_arg_with_pretty_repr(val: Any):
    """
    Replace an argument with a pretty representation- note that this does NOT mean actually calling .pretty_repr(), as
    we don't want to get a full pretty repr (x = pasten), but just a name, and if not then a pretty value

    If it's not a quib, just return it's repr
    """
    from pyquibbler.quib.quib import Quib
    if not isinstance(val, Quib):
        converter = ITEMS_TO_CONVERTERS.get(type(val), repr)
        return converter(val)

    if val.name is not None:
        return val.name
    return val.get_functional_representation_expression()


def getitem_converter(func, pretty_arg_names: List[str]):
    assert len(pretty_arg_names) == 2
    return f"{pretty_arg_names[0]}[{pretty_arg_names[1]}]"


def call_converter(func, pretty_arg_names: List[str]):
    func_being_called, *args = pretty_arg_names
    return f"{func_being_called}({', '.join(args)})"


def get_pretty_args_and_kwargs(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    pretty_args = [recursively_run_func_on_object(replace_arg_with_pretty_repr, arg,
                                                  iterable_func=_convert_iterable,
                                                  slice_func=_convert_slice) for arg in args]
    pretty_kwargs = [f'{key}={replace_arg_with_pretty_repr(val)}' for key, val in kwargs.items()]

    return pretty_args, pretty_kwargs


def get_pretty_value_of_func_with_args_and_kwargs(func: Callable,
                                                  args: Tuple[Any, ...],
                                                  kwargs: Mapping[str, Any]) -> Union[MathExpression, str]:
    """
    Get the pretty value of a function, using a special converter if possible (eg for math notation) and defaulting
    to a standard func(xxx) if not
    """
    pretty_args, pretty_kwargs = get_pretty_args_and_kwargs(args, kwargs)
    # For now, no ability to special convert if kwargs exist
    if not pretty_kwargs and func in CONVERTERS:
        pretty_value = CONVERTERS[func](func, pretty_args)
    else:
        func_name = getattr(func, '__name__', str(func))
        pretty_value = f'{func_name}({", ".join(map(str, [*pretty_args, *pretty_kwargs]))})'

    return pretty_value


CONVERTERS = {
    **MATH_FUNCS_TO_CONVERTERS,
    operator.getitem: getitem_converter,
    np.vectorize.__call__: call_converter
}
