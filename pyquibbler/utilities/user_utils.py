from pathlib import Path
from typing import Union, List, Callable, Type
from types import ModuleType

from pyquibbler.project import Project

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib

import functools

copy_docs = functools.partial(functools.wraps, assigned=['__doc__'], updated=[])


def q(func, *args, **kwargs) -> Quib:
    """
    Creates a function quib from the given function call.
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
def save_quibs(save_as_txt: Optional[bool] = None):
    Project.get_or_create().save_quibs(save_as_txt=save_as_txt)


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


def redraw_central_refresh_graphics_function_quibs() -> None:
    """
    Redraw all graphics function quibs which only redraw when set to UpdateType.CENTRAL
    """
    return Project.get_or_create().redraw_central_refresh_graphics_function_quibs()


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
    return hasattr(func, '__quibbler_wrapped__')
