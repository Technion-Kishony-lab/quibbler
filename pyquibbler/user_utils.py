from pathlib import Path
from typing import Union

from pyquibbler.input_validation_utils import validate_user_input
from pyquibbler.project import Project
from pyquibbler.quib import GraphicsFunctionQuib

from pyquibbler.quib import Quib


def q(func, *args, **kwargs) -> Quib:
    """
    Creates a function quib from the given function call.
    """
    # In case the given function is already a wrapper for a specific quib type, we use it.
    quib_type = getattr(func, '__quib_wrapper__', GraphicsFunctionQuib)
    return quib_type.create(func=func, func_args=args, func_kwargs=kwargs, evaluate_now=False)


def q_eager(func, *args, **kwargs) -> Quib:
    """
    Creates a graphical function quib from the given function call.
    """
    # In case the given function is already a wrapper for a specific quib type, we use it.
    quib_type = getattr(func, '__quib_wrapper__', GraphicsFunctionQuib)
    return quib_type.create(func=func, func_args=args, func_kwargs=kwargs, evaluate_now=True)


def reset_impure_function_quibs() -> None:
    """
    Resets all impure function quib caches and invalidates and redraws with them- note that this does NOT necessarily
    mean they will run
    """
    Project.get_or_create().reset_invalidate_and_redraw_all_impure_function_quibs()


@validate_user_input(path=(str, Path))
def set_project_path(path: Union[str, Path]) -> None:
    """
    Set the current project's path
    """
    if isinstance(path, str):
        path = Path(path)
    Project.get_or_create().path = path


def load_quibs() -> None:
    """
    Load quibs from files of project if existing
    """
    Project.get_or_create().load_quibs()


def save_quibs(save_iquibs_as_txt_where_possible: bool = True):
    """
    Save all the quibs to files (if relevant- ie if they have overrides)
    """
    Project.get_or_create().save_quibs(save_iquibs_as_txt_where_possible=save_iquibs_as_txt_where_possible)


def undo() -> None:
    """
    Undo the last action commited (an assignment or assignment removal)
    """
    Project.get_or_create().undo()


def redo() -> None:
    """
    Redo the last action undone
    """
    Project.get_or_create().redo()


def has_undos() -> bool:
    """
    Whether or not any undos exist
    """
    return Project.get_or_create().has_undo()


def has_redos() -> bool:
    """
    Whether or not any redos exist
    """
    return Project.get_or_create().has_redo()


def redraw_central_refresh_graphics_function_quibs() -> None:
    """
    Redraw all graphics function quibs which only redraw when set to UpdateType.CENTRAL
    """
    return Project.get_or_create().redraw_central_refresh_graphics_function_quibs()
