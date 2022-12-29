from contextlib import contextmanager
from .project import Project
from ..quib.graphics.redraw import is_dragging

IN_UNDO_GROUP_MODE = False


def is_undo_group_mode():
    return IN_UNDO_GROUP_MODE


@contextmanager
def undo_group_mode(temporarily: bool = False):
    global IN_UNDO_GROUP_MODE
    if IN_UNDO_GROUP_MODE:
        yield
    IN_UNDO_GROUP_MODE = True
    project = Project.get_or_create()
    try:
        project.start_pending_undo_group()
        yield
    except Exception:
        project.undo_pending_group(False)
    else:
        if not temporarily:
            if is_dragging():
                project.squash_pending_group_into_last_undo()
            else:
                project.push_pending_undo_group_to_undo_stack()
    finally:
        IN_UNDO_GROUP_MODE = False
