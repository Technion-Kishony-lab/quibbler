from pathlib import Path
from typing import Union

from pyquibbler.project import Project


def copy_docs(original):

    def _wrapper(func):
        func.__doc__ = original.__doc__
        return func

    return _wrapper


# copy_docs = functools.partial(functools.wraps, assigned=['__doc__'], updated=[])


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
