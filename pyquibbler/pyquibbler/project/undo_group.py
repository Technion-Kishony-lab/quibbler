from contextlib import contextmanager
from .project import Project
from pyquibbler.quib.graphics.graphics_assignment_mode import is_within_graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import is_dragging

IN_UNDO_GROUP_MODE = False


@contextmanager
def undo_group_mode(temporarily: bool = False):
    """
    if an exception occurs, undo changes.
    return bool indicating if completed without exception
    """

    global IN_UNDO_GROUP_MODE
    if IN_UNDO_GROUP_MODE:
        yield
    else:
        IN_UNDO_GROUP_MODE = True
        project = Project.get_or_create()
        try:
            project.start_pending_undo_group()
            yield
        except Exception:
            if is_within_graphics_assignment_mode():
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
