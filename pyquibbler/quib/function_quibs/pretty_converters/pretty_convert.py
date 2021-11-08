import operator
from typing import Callable, List, Union
from typing import Tuple, Any, Mapping

from pyquibbler.quib.function_quibs.pretty_converters.convert_math_equations import MATH_FUNCS_TO_CONVERTERS, \
    MathExpression


def _convert_slice(slice_: slice):
    pretty = ':'
    if slice_.start:
        pretty = f"{slice_.start}{pretty}"
    if slice_.stop:
        pretty = f"{pretty}{slice_.stop}"
    if slice_.step:
        pretty = f"{pretty}:{slice_.step}"
    return pretty


ITEMS_TO_CONVERTERS = {
    slice: _convert_slice,
    type(...): lambda *_: '...'
}


def replace_arg_with_pretty_repr(val: Any):
    """
    Replace an argument with a pretty representation- note that this does NOT mean actually calling .pretty_repr(), as
    we don't want to get a full pretty repr (x = pasten), but just a name, and if not then a pretty value

    If it's not a quib, just return it's repr
    """
    from pyquibbler.quib import Quib
    if not isinstance(val, Quib):
        converter = ITEMS_TO_CONVERTERS.get(type(val), repr)
        return converter(val)

    if val.name is not None:
        return val.name
    return val.get_pretty_functional_representation()


def getitem_converter(func, pretty_arg_names: List[str]):
    assert len(pretty_arg_names) == 2
    return f"{pretty_arg_names[0]}[{pretty_arg_names[1]}]"


def get_pretty_value_of_func_with_args_and_kwargs(func: Callable,
                                                  args: Tuple[Any, ...],
                                                  kwargs: Mapping[str, Any]) -> Union[MathExpression, str]:
    """
    Get the pretty value of a function, using a special converter if possible (eg for math notation) and defaulting
    to a standard func(xxx) if not
    """
    # For now, no ability to special convert if kwargs exist
    arg_names = [replace_arg_with_pretty_repr(arg) for arg in args]
    kwarg_names = [f'{key}={replace_arg_with_pretty_repr(val)}' for key, val in kwargs.items()]

    if not kwarg_names and func in CONVERTERS:
        pretty_value = CONVERTERS[func](func, arg_names)
    else:
        func_name = getattr(func, '__name__', str(func))
        pretty_value = f'{func_name}({", ".join(map(str, [*arg_names, *kwarg_names]))})'

    return pretty_value


CONVERTERS = {
    **MATH_FUNCS_TO_CONVERTERS,
    operator.getitem: getitem_converter
}
