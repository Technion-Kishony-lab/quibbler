import functools
from pathlib import Path
from typing import Union, List, Callable, Type, Optional, Any
from types import ModuleType

from pyquibbler.project import Project
from pyquibbler.quibapp import QuibApp

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib


def copy_docs(original):

    def _wrapper(func):
        func.__doc__ = original.__doc__
        return func

    return _wrapper


# copy_docs = functools.partial(functools.wraps, assigned=['__doc__'], updated=[])


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


def obj2quib(obj: Any) -> Quib:
    """
    Create a quib from an object containing quibs.

    Convert an object containing quibs to a quib whose value represents the object.

    Parameters
    ----------
    obj : any object
        The object to convert to quib. Can contain nested lists, tuples, dicts and quibs.

    See also
    --------
    quiby, q, iquib

    Examples
    --------
    >>> a = iquib(3)
    >>> my_list = obj2quib([1, 2, a, 4])
    >>> a.assign(7)
    >>> my_list.get_value()
    [1, 2, 7, 4]

    Note
    ----
    If the argument obj is a quib, the function returns this quib.
    """

    # TODO: need to implement translation and inversion for list, tuple and dict.
    if isinstance(obj, (list, tuple)):
        return q(type(obj), [obj2quib(sub_obj) for sub_obj in obj])

    if isinstance(obj, dict):
        return q(dict, [(obj2quib(sub_key), obj2quib(sub_obj)) for sub_key, sub_obj in obj.items()])

    return obj


def get_project() -> Project:
    """
    Returns the current project.

    A project allows controlling common functionality for all quibs, like save/load, undo/redo.

    See Also
    --------
    Project
    """
    return Project.get_or_create()


@copy_docs(Project.reset_random_quibs)
def reset_random_quibs() -> None:
    Project.get_or_create().reset_random_quibs()


@copy_docs(Project.reset_file_loading_quibs)
def reset_file_loading_quibs() -> None:
    Project.get_or_create().reset_file_loading_quibs()


@copy_docs(Project.reset_impure_quibs)
def reset_impure_quibs() -> None:
    Project.get_or_create().reset_impure_quibs()


def get_project_directory() -> Path:
    """
    Returns the directory to which quib assignments are saved.

    By default, quibs save their override data to the project directory, or to a directory relative to
    this project directory, as specified by each quib `save_directory` property.

    None indicates undefined path.

    Returns
    -------
    PathWithHyperLink or None

    See Also
    --------
    Quib.save_directory, pyquibbler.set_project_directory
    """
    return Project.get_or_create().directory


def set_project_directory(directory: Union[None, str, Path]) -> None:
    """
    Set the current project's directory.

    By default, quibs save their override data to the project directory, or to a directory relative to
    this project directory, as specified by each quib `save_directory` property.

    `None` indicates undefined path.

    Parameters
    ----------
    directory: str, pathlib.Path or None

    See Also
    --------
    Quib.save_directory, pyquibbler.get_project_directory
    """
    Project.get_or_create().directory = directory


@copy_docs(Project.load_quibs)
def load_quibs() -> None:
    Project.get_or_create().load_quibs()


@copy_docs(Project.save_quibs)
def save_quibs():
    Project.get_or_create().save_quibs()


@copy_docs(Project.sync_quibs)
def sync_quibs():
    Project.get_or_create().sync_quibs()


@copy_docs(Project.undo)
def undo() -> None:
    Project.get_or_create().undo()


@copy_docs(Project.redo)
def redo() -> None:
    Project.get_or_create().redo()


@copy_docs(Project.can_undo)
def can_undo() -> bool:
    return Project.get_or_create().can_undo()


@copy_docs(Project.can_redo)
def can_redo() -> bool:
    return Project.get_or_create().can_redo()


@copy_docs(Project.refresh_graphics)
def refresh_graphics() -> None:
    return Project.get_or_create().refresh_graphics()


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


def quibapp():
    """
    Open the Quibbler App

    See Also
    --------
    Project
    """
    return QuibApp.get_or_create()
