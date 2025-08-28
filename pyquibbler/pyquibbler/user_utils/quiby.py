import functools
from typing import Callable, Optional

from pyquibbler.function_overriding.is_initiated import warn_if_quibbler_not_initialized, is_quibbler_initialized
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.find_quibs import get_quibs_or_sources_locations_in_args_kwargs
from pyquibbler.quib.factory import create_quib as create_quib_func
from pyquibbler.quib.get_value_context_manager import get_value_context_pass_quibs

from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
from pyquibbler.user_utils.quiby_methods import get_all_quibifiable_attributes


def not_quiby(func: Callable) -> Callable:
    """
    Decorator to mark a method as not quiby, when used inside a quiby-decorated class.

    Marks the given method as not quiby, so that when used inside a quiby-decorated class,

    Examples
    --------
    >>> from pyquibbler import quiby, not_quiby
    >>>
    >>> @quiby
    ... class MyClass:
    ...     def method(self):
    ...         ...
    ...
    ...     @not_quiby
    ...     def helper(self):
    ...         ...
    ...
    >>> obj = MyClass()
    >>> obj.method  # This is a quiby method
    >>> obj.helper  # This is a regular method

    Note
    ----
    This decorator has no effect when used outside a quiby-decorated class.

    See Also
    --------
    quiby
    """
    setattr(func, '__not_quiby__', True)
    return func


def quiby(func: Callable = None,
          lazy: Optional[bool] = None,
          pass_quibs: bool = False,
          is_random: bool = False,
          is_graphics: Optional[bool] = False,
          is_file_loading: bool = False,
          create_quib: Optional[bool] = None,
          _quibify_even_if_quibbler_not_initialized: bool = False,
          **kwargs,
          ) -> Callable[..., Quib]:
    """
    Convert a regular function into a quiby function.

    Converts any function `func` to a function that can work on quib arguments ("quiby" function).
    When such quiby function is called, it creates a function quib that implement
    the original function.

    For classes, applies quiby behavior to all methods and properties (instance methods, class methods, static methods, and properties).

    `quiby` can also be used as a decorator of user functions or classes, either directly, or as a function with
    parameter specification (see examples).

    Parameters
    ----------
    func : Callable or Type
        The function or class to convert.

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

    create_quib : bool or None, default: True
        Controls when to create a quib:
        - True: Always create a quib.
        - False: Never create a quib, return the normal function output.
        - None: Automatic (default) - create a quib only if arguments contain quibs.

    Returns
    -------
    Callable
        a quiby function, or a quiby decorator (if function is not specified)

    See Also
    --------
    is_quiby, q, not_quiby
    initialize_quibbler
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
    >>> display_num = display_variable('number', num)
    >>> display_num.get_value()
    'number = 7'

    >>> @quiby(pass_quibs=False)  # default for all methods in the class
    ... class MyClass:
    ...     def __init__(self, x, y, z):
    ...         self.x = x  # quib
    ...         self.y = y  # quib
    ...
    ...     def get_x(self):
    ...         return self.x  # Gets value (x.get_value())
    ...
    ...     @quiby(pass_quibs=True)  # override for this method only
    ...     def get_y(self):
    ...         return self.y  # Gets proxy quib (proxy(y))
    ...

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

    Note
    ----
    If Quibbler has not been initialized, `quiby` will simply return the unmodified function, not a quiby function.
    This allows checking how your code works without quibs.
    """

    if func is None:
        return functools.partial(quiby,
                                 lazy=lazy,
                                 pass_quibs=pass_quibs,
                                 is_random=is_random,
                                 is_graphics=is_graphics,
                                 is_file_loading=is_file_loading,
                                 create_quib=create_quib,
                                 _quibify_even_if_quibbler_not_initialized=_quibify_even_if_quibbler_not_initialized,
                                 **kwargs,
                                 )

    if not is_quibbler_initialized() and not _quibify_even_if_quibbler_not_initialized:
        warn_if_quibbler_not_initialized()
        return func

    # Handle class decoration.

    # Check if this is a user-defined class (avoid builtins like str, list, etc.)
    if isinstance(func, type) and getattr(func, "__module__", "") != "builtins":
        return quiby_class(func, lazy=lazy, pass_quibs=pass_quibs, is_random=is_random,
                           is_graphics=is_graphics, is_file_loading=is_file_loading, 
                           create_quib=create_quib, **kwargs)

    # Handle function decoration

    from pyquibbler.function_definitions import get_definition_for_function

    func_definition = get_definition_for_function(func, return_default=False)
    if func_definition is None:
        func_definition = create_or_reuse_func_definition(
            lazy=lazy,
            pass_quibs=pass_quibs,
            is_random=is_random,
            is_graphics=is_graphics,
            is_file_loading=is_file_loading,
            search_quibs_in_attributes=True,
            **kwargs,
        )

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        if create_quib is True or is_graphics is True:
            # Always create a quib
            return create_quib_func(func=func, args=args, kwargs=kwargs, func_definition=func_definition)
        if create_quib is False:
            # Never create a quib, just call the function (the function may still return a quib by itself)
            return func(*args, **kwargs)
        else:  # create_quib is None
            # Automatic: create quib only if args contain quibs and context allows it

            if get_value_context_pass_quibs() is not False:
                quib_locations = get_quibs_or_sources_locations_in_args_kwargs(
                    Quib, args, kwargs, search_in_attributes=True)
                
                if quib_locations:
                    return create_quib_func(func=func, args=args, kwargs=kwargs, func_definition=func_definition,
                                            quib_locations=quib_locations)
            
            return func(*args, **kwargs)

    _wrapper.func_definition = func_definition
    _wrapper.__quibbler_wrapped__ = func

    return _wrapper


def quiby_class(cls, *args, **kwargs):
    """Apply quiby to all methods and properties of a user-defined class."""

    for attr in get_all_quibifiable_attributes(cls):
        # Each wrapper function handles extraction, wrapping, and recreation
        quiby_attribute = attr.wrapper_func(attr.attribute, quiby, *args, **kwargs)
        setattr(cls, attr.name, quiby_attribute)

    return cls


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

    Note
    ----
    If Quibbler has not been initialized, `q` will simply evaluate the function and return the result.
    By not initializing quibbler you can thereby check how your code works without quibs.
    """

    if not is_quibbler_initialized():
        warn_if_quibbler_not_initialized()
        return func(*args, **kwargs)

    return create_quib_func(func=func, args=args, kwargs=kwargs)
