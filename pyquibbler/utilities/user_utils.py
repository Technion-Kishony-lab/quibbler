from pathlib import Path
from typing import Union, List, Callable, Type, Optional
from types import ModuleType

from pyquibbler import quiby_function
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


def quiby(func: Callable,
          lazy: Optional[bool] = None,
          pass_quibs: bool = False,
          is_random: bool = False,
          is_graphics: Optional[bool] = False,
          is_file_loading: bool = False
          ):

    """
    Convert a regular function into a quiby function.

    Converts any function `func` to a quiby function - a function that can work
    on quib arguments. When such quiby function is called, it creates a functional quib that implement
    the original function.

    Parameters
    ----------
    func : Callable
        The function to convert.

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

    Returns
    -------
    Callable
        a quiby function

    See Also
    --------
    quiby_function, is_quiby, q

    Examples
    --------
    >>> a = iquib(2)
    >>> b = quiby(str)(a)

    >>> b.get_value()
    '2'
    """

    return quiby_function(
        lazy=lazy,
        pass_quibs=pass_quibs,
        is_random=is_random,
        is_graphics=is_graphics,
        is_file_loading=is_file_loading,
    )(func)


def q(func, *args, **kwargs) -> Quib:
    """
    Creates a function quib from the given function call.

    Returns
    -------
    Quib

    See Also
    --------
    quiby, quiby_function, is_quiby, q

    Examples
    --------
    >>> a = iquib(2)
    >>> b = q(str, a)

    >>> b.get_value()
    '2'
    """
    return create_quib(func=func, args=args, kwargs=kwargs)


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


@copy_docs(Project.directory)
def get_project_directory() -> Path:
    return Project.get_or_create().directory


def set_project_directory(directory: Union[None, str, Path]) -> None:
    """
    Set the current project's directory

    path can be a string, or a Path object, or None indicating that a path is not yet set.
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
    return [f"{getattr(mdl, '__name__', mdl)}: {func_name}" for definition, mdl, func_name, isoverriden in
            FUNCS_TO_DEFINITIONS_MODULE_NAME_ISOVERRIDDEN.values()
            if isoverriden and (module_or_cls is None or mdl is module_or_cls)
            and mdl is not QVectorize]


def is_quiby(func: Callable) -> bool:
    """
    Check whether a given function is modified to work directly with quib arguments ("quiby").

    Returns
    -------
    bool

    See Also
    --------
    q, quiby, quiby_function, list_quiby_funcs

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
