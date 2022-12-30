from contextlib import contextmanager
from .project import Project
from pyquibbler.quib.graphics.graphics_assignment_mode import is_within_graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import is_dragging
from ..utilities.basic_types import Flag

IN_UNDO_GROUP_MODE = False


def is_undo_group_mode():
    return IN_UNDO_GROUP_MODE


@contextmanager
def undo_group_mode(temporarily: bool = False):
    """
    if an exception occurs, undo changes.
    return bool indicating if completed without exception
    """

    global IN_UNDO_GROUP_MODE
    if IN_UNDO_GROUP_MODE:
        yield
    IN_UNDO_GROUP_MODE = True
    project = Project.get_or_create()
    all_ok = Flag(True)
    try:
        project.start_pending_undo_group()
        yield all_ok
    except Exception:
        if is_within_graphics_assignment_mode():
            all_ok.set(False)
            project.undo_pending_group(False)
        else:
            raise
    else:
        if not temporarily:
            if is_dragging():
                project.squash_pending_group_into_last_undo()
            else:
                project.push_pending_undo_group_to_undo_stack()
    finally:
        IN_UNDO_GROUP_MODE = False
