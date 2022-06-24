import functools
from typing import Optional, Callable

from pyquibbler.quib.factory import create_quib


def quiby_function(
        lazy: Optional[bool] = None,
        pass_quibs: bool = False,
        is_random: bool = False,
        is_graphics: Optional[bool] = False,
        is_file_loading: bool = False):
    """
    Decorator for converting a regular function into a quiby function.

    Decorating a user function with this decorator returns a quiby function - a function that can work
    on quib arguments. When such quiby function is called, it creates a functional quib that implement
    the original function.

    Parameters
    ----------
    lazy : bool, optional
        Indicates whether the created functional quib evaluates immediately (lazy=False), or only when
        it's value requested (lazy=True). When lazy=None, the function is evaluated immediately only if
        it is a declared graphics function (is_graphics=True).

    pass_quibs : bool, default False
        Indicates whether the function is called with quib arguments (pass_quibs=True), or with the
        quib arguments replaced with their values (pass_quibs=False, default).

    is_random : bool, default False
        Indicates a random funcxtion. Random functions are automatically cached and can be invalidated
        centrally to re-randomize.

    is_graphics : bool or None
        Specifies whether the function creates graphics. Any graphics created in this function
        will also be redrawn if any upstream quib changes (according to the quibs `graphics_update`).
        is_graphics=None (default) will search for graphics and define the quib as a graphics quib if
        any graphics was created.

    is_file_loading : bool
        Indicates whether the function's returnsed value depends on an external file.
    """

    from pyquibbler.function_definitions.func_definition import FuncDefinition
    from pyquibbler.function_definitions import get_definition_for_function

    def _decorator(func: Callable):
        func_definition = get_definition_for_function(func, return_default=False)
        func_definition = func_definition or FuncDefinition(func=func,
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

    return _decorator
