from pathlib import Path
from typing import Union, List, Callable, Type
from types import ModuleType

from pyquibbler.project import Project
from pyquibbler.quibapp import QuibApp

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib

import functools

copy_docs = functools.partial(functools.wraps, assigned=['__doc__'], updated=[])


def q(func, *args, **kwargs) -> Quib:
    """
    Creates a function quib from the given function call.

    Example:
        a = iquib(2)
        b = q(str, a)

        b.get_value() -> '2'

    Returns:
        Quib
    """
    return create_quib(func=func, args=args, kwargs=kwargs, evaluate_now=False)


def q_eager(func, *args, **kwargs) -> Quib:
    """
    Creates a graphical function quib from the given function call.
    """
    return create_quib(func=func, func_args=args, func_kwargs=kwargs, evaluate_now=True)


def get_project() -> Project:
    """
    Returns the current project.

    A project allows controlling common functionality for all quibs, like save/load, undo/redo.
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
    Returns a list of overridden, "quiby", functions

    module_or_cls: optinal specification of module (like, numpy, matplotlib, matplotlib.widgets)
    """
    from pyquibbler.function_definitions.definitions import FUNCS_TO_DEFINITIONS_MODULE_AND_NAME_ISOVERRIDDEN
    from pyquibbler.function_overriding.third_party_overriding.numpy.vectorize_overrides import QVectorize
    return [f"{getattr(mdl, '__name__', mdl)}: {func_name}" for definition, mdl, func_name, isoverriden in
            FUNCS_TO_DEFINITIONS_MODULE_AND_NAME_ISOVERRIDDEN.values()
            if isoverriden and (module_or_cls is None or mdl is module_or_cls)
            and mdl is not QVectorize]


def is_func_quiby(func: Callable) -> bool:
    """
    Check whether a given function is modified to work directly with quib arguments ("quiby").

    Returns:
        bool

    Example:
        is_func_quiby(np.sin) -> True
        is_func_quiby(len) -> False

    See also:
        q, q_eager
    """
    return hasattr(func, '__quibbler_wrapped__')


def quibapp():
    """
    Open the Quibbler App
    """
    return QuibApp.get_or_create()
