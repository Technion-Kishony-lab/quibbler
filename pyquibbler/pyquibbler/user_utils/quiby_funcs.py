import functools
from types import ModuleType
from typing import Union, Type, List, Callable, Optional

from pyquibbler.function_overriding.is_initiated import warn_if_quibbler_not_initiated
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib


def list_quiby_funcs(module_or_cls: Union[None, ModuleType, Type] = None) -> List[str]:
    """
    List quiby functions.

    Returns a list of string descriptions of all functions overridden to be able to work with quib arguments.

    Parameters
    ----------
    module_or_cls: ModuleType, optional (default: None)
        Specifies a module (numpy, matplotlib, ipywidgets). When specified, only functions belonging to the indicated
        module are listed.
    """
    warn_if_quibbler_not_initiated()

    from pyquibbler.function_definitions.definitions import FUNCS_TO_FUNC_INFO
    from pyquibbler.function_overriding.third_party_overriding.numpy.vectorize_overrides import QVectorize
    from pyquibbler.function_overriding.override_all import ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES
    return \
        [f"{getattr(func_info.module_or_cls, '__name__', func_info.module_or_cls)}: {func_info.func_name}"
         for func_info in FUNCS_TO_FUNC_INFO.values()
         if func_info.is_overridden and (module_or_cls is None or func_info.module_or_cls is module_or_cls)
         and func_info.module_or_cls is not QVectorize] \
        + [f"np.ndarray.{attribute}" for attribute in ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES]


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
    warn_if_quibbler_not_initiated()

    return hasattr(func, '__quibbler_wrapped__')


def quiby(func: Callable = None,
          lazy: Optional[bool] = None,
          pass_quibs: bool = False,
          is_random: bool = False,
          is_graphics: Optional[bool] = False,
          is_file_loading: bool = False,
          **kwargs,
          ) -> Callable[..., Quib]:
    """
    Convert a regular function into a quiby function.

    Converts any function `func` to a function that can work on quib arguments ("quiby" function).
    When such quiby function is called, it creates a function quib that implement
    the original function.

    `quiby` can also be used as a decorator of user functions, either directly, or as a function with
    parameter specification (see examples).

    Parameters
    ----------
    func : Callable
        The function to convert.

    lazy : bool or None, default None
        Indicates whether the created function quib evaluates immediately (`lazy=False`), or only when
        its value is requested (`lazy=True`). When `lazy=None` (default), the function is evaluated immediately
        only if it is a declared graphics function (`is_graphics=True`).

    pass_quibs : bool, default False
        Indicates whether the function should be called with quib arguments (`pass_quibs=True`), or with the
        values of the quib arguments (`pass_quibs=False`, default).

    is_random : bool, default False
        Indicates a random function. Random functions are automatically cached and can be invalidated
        centrally to re-randomize (see `reset_random_quibs`).

    is_graphics : bool or None, default: False
        Specifies whether the function creates graphics. If `True`, the function will be re-evaluated upon any
        upstream quib changes (according to the quib's `graphics_update` property), and any graphics it creates
        will be redrawn.
        `is_graphics=None` will search for graphics during the call to the function and the quib will
        automatically be defined as a graphics quib if any graphics was created.

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

    warn_if_quibbler_not_initiated()

    if func is None:
        return functools.partial(quiby,
                                 lazy=lazy,
                                 pass_quibs=pass_quibs,
                                 is_random=is_random,
                                 is_graphics=is_graphics,
                                 is_file_loading=is_file_loading,
                                 **kwargs,
                                 )
    else:
        from pyquibbler.function_definitions import get_definition_for_function

        func_definition = get_definition_for_function(func, return_default=False)
        if func_definition is None:
            from pyquibbler.function_definitions.func_definition import FuncDefinition
            func_definition = FuncDefinition(lazy=lazy,
                                             pass_quibs=pass_quibs,
                                             is_random=is_random,
                                             is_graphics=is_graphics,
                                             is_file_loading=is_file_loading,
                                             **kwargs,
                                             )

        @functools.wraps(func)
        def _wrapper(*args, **kwargs) -> Quib:
            return create_quib(func=func, args=args, kwargs=kwargs, func_definition=func_definition)

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

    warn_if_quibbler_not_initiated()

    return create_quib(func=func, args=args, kwargs=kwargs)
