from pyquibbler.assignment.override_choice.types import reset_all_override_group, is_reset_all_override_group
from pyquibbler.project.undo_group import reset_all_undo_group, is_reset_all_undo_group
from pyquibbler.quib.get_value_context_manager import reset_all_get_value_context, is_reset_all_get_value_context
from pyquibbler.quib.graphics.graphics_assignment_mode import reset_all_graphics_assignment_mode, \
    is_reset_all_graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import reset_all_redraw, is_reset_all_redraw


def reset_all():
    """
    Reset all global variables to their initial state
    """
    reset_all_graphics_assignment_mode()
    reset_all_undo_group()
    reset_all_redraw()
    reset_all_override_group()
    reset_all_get_value_context()


def is_reset_all():
    return is_reset_all_graphics_assignment_mode() \
        and is_reset_all_undo_group() \
        and is_reset_all_redraw() \
        and is_reset_all_override_group() \
        and is_reset_all_get_value_context()
