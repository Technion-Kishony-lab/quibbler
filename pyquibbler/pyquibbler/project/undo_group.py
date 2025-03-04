from contextlib import contextmanager
from .project import Project
from pyquibbler.quib.graphics.graphics_assignment_mode import is_within_graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import is_dragging

IN_UNDO_GROUP_MODE = False


@contextmanager
def undo_group_mode(temporarily: bool = False):

    global IN_UNDO_GROUP_MODE
    if IN_UNDO_GROUP_MODE:
        yield
        return

    IN_UNDO_GROUP_MODE = True
    project = Project.get_or_create()
    project.start_pending_undo_group()
    try:
        yield
    except Exception:
        if is_within_graphics_assignment_mode():
            project.undo_pending_group(False)
        else:
            project.push_pending_undo_group_to_undo_stack()
            raise
    else:
        if temporarily:
            project.undo_pending_group(True)
        else:
            if is_dragging():
                project.squash_pending_group_into_last_undo()
            else:
                project.push_pending_undo_group_to_undo_stack()
    finally:
        IN_UNDO_GROUP_MODE = False
