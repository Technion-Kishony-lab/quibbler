import functools
from types import ModuleType
from typing import Union, Type, List, Callable, Optional

from .project_wraps import reset_random_quibs
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib


def list_quiby_funcs(module_or_cls: Union[None, ModuleType, Type] = None) -> List[str]:
    """
    Returns a list of "quiby" functions.

    Returns a list of functions overridden to be able to work with quib arguments.
    """
    from pyquibbler.function_definitions.definitions import FUNCS_TO_DEFINITIONS_MODULE_NAME_ISOVERRIDDEN
    from pyquibbler.function_overriding.third_party_overriding.numpy.vectorize_overrides import QVectorize
    return [f"{getattr(mdl, '__name__', mdl)}: {func_name}" for definition, mdl, func_name, isoverridden in
            FUNCS_TO_DEFINITIONS_MODULE_NAME_ISOVERRIDDEN.values()
            if isoverridden and (module_or_cls is None or mdl is module_or_cls)
            and mdl is not QVectorize]


def is_quiby(func: Callable) -> bool:
    """
    Check whether a given function is modified to work directly with quib arguments ("quiby").

    Returns
    -------
    bool

    See Also
    --------
    q, quiby, list_quiby_funcs

    Examples
    --------
    >>> is_quiby(np.sin)  # -> True
    >>> is_quiby(len)  # -> False
    """
    return hasattr(func, '__quibbler_wrapped__')


def quiby(func: Callable = None,
          lazy: Optional[bool] = None,
          pass_quibs: bool = False,
          is_random: bool = False,
          is_graphics: Optional[bool] = False,
          is_file_loading: bool = False
          ):
    """
    Convert a regular function into a quiby function.

    Converts any function `func` to a function that can work on quib arguments (quiby function.
    When such quiby function is called, it creates a function quib that implement
    the original function.

    quiby can also be used as a decorator of user functions, either directly without parameters, or with
    parameter specification (see examples).

    Parameters
    ----------
    func : Callable
        The function to convert.

    lazy : bool or None, default None
        Indicates whether the created function quib evaluates immediately (lazy=False), or only when
        its value is requested (lazy=True). When lazy=None (default), the function is evaluated immediately
        only if it is declared as a graphics function (is_graphics=True).

    pass_quibs : bool, default False
        Indicates whether the function is called with quib arguments (pass_quibs=True), or with the
        values of the quib arguments (pass_quibs=False, default).

    is_random : bool, default False
        Indicates a random function. Random functions are automatically cached and can be invalidated
        centrally to re-randomize (see reset_random_quibs).

    is_graphics : bool or None, default: False
        Specifies whether the function creates graphics. If True, the function will be re-evaluated upon any
        upstream quib changes (according to the quib's `graphics_update`), and any graphics it creates
        will be redrawn.
        is_graphics=None will search for graphics and define the quib as a graphics quib if
        any graphics was created.

    is_file_loading : bool, default: False
        Indicates whether the function's returned value depends on reading of an external file.
        File-loading functions can be invalidated centrally to re-load (see reset_file_loading_quibs).

    Returns
    -------
    Callable
        a quiby function, or a quiby decorator (if function is not specified)

    See Also
    --------
    is_quiby, q
    Quib.graphics_update, Quib.is_graphics, Quib.is_random, Quib.is_file_loading
    reset_random_quibs, reset_file_loading_quibs

    Examples
    --------
    >>> a = iquib(2)
    >>> b = quiby(str)(a)
    >>> b.get_value()
    '2'

    >>> @quiby
    ... def display_variable(name: str, x:int):
    ...     return f'{name} = {x}'
    ...
    >>> num = iquib(7)
    >>> display_num = display_variable('num', num)
    >>> display_num.get_value()
    'x = 7'

    >>> @quiby(is_random=True)
    ... def sum_of_dice(n: int):
    ...     dice = np.random.randint(1, 6, n)
    ...     return np.sum(dice)
    ...
    >>> n = iquib(2)
    >>> sum_dice = sum_of_dice(n)
    >>> sum_dice.get_value()
    17
    >>> reset_random_quibs()
    >>> sum_dice.get_value()
    27
    """

    if func is None:
        return functools.partial(quiby,
                                 lazy=lazy,
                                 pass_quibs=pass_quibs,
                                 is_random=is_random,
                                 is_graphics=is_graphics,
                                 is_file_loading=is_file_loading,
                                 )
    else:
        from pyquibbler.function_definitions import get_definition_for_function

        func_definition = get_definition_for_function(func, return_default=False)
        if func_definition is None:
            from pyquibbler.function_definitions.func_definition import FuncDefinition
            func_definition = FuncDefinition(func=func,
                                             lazy=lazy,
                                             pass_quibs=pass_quibs,
                                             is_random=is_random,
                                             is_graphics=is_graphics,
                                             is_file_loading=is_file_loading,
                                             )

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return create_quib(func=None, args=args, kwargs=kwargs, func_definition=func_definition)

        _wrapper.func_definition = func_definition

        return _wrapper


def q(func, *args, **kwargs) -> Quib:
    """
    Creates a function quib from the given function call.

    ``w = q(func, *args, **kwargs)`` returns a quib that implement ``func(*args, **kwargs)``.

    Returns
    -------
    Quib

    See Also
    --------
    quiby, is_quiby, q

    Examples
    --------
    >>> a = iquib(2)
    >>> b = q(str, a)
    >>> b.get_value()
    '2'
    """
    return create_quib(func=func, args=args, kwargs=kwargs)
