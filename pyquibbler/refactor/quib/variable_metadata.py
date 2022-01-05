
import ast
from dataclasses import dataclass
from typing import Optional

from varname.utils import ASSIGN_TYPES, get_node, node_name, AssignType

from pyquibbler.refactor.exceptions import PyQuibblerException


class CannotFindNodeException(PyQuibblerException):
    pass


AST_ASSIGNMENTS_TO_VAR_NAME_STATES = {}


@dataclass
class VarNameState:
    total_var_count: int
    current_var_count: int


def find_relevant_parent_assignment_node(node: ast.AST) -> AssignType:
    """Look for an ast.Assign node in the parents"""
    if hasattr(node, 'parent'):
        node = node.parent
        if isinstance(node, ASSIGN_TYPES):
            return node
        if isinstance(node, ast.Tuple) and hasattr(node, 'parent') and isinstance(node.parent, ASSIGN_TYPES):
            return node.parent
    return None


def get_quib_node_being_set_outside_of_pyquibbler():
    import pyquibbler
    import matplotlib
    return get_node(frame=1, ignore=[pyquibbler, matplotlib], raise_exc=False)


def get_file_name_and_line_number_of_quib():
    refnode = get_quib_node_being_set_outside_of_pyquibbler()
    if refnode is None:
        return None, None
    frame = refnode.__frame__
    file_name = frame.f_code.co_filename
    line_number = frame.f_lineno
    return file_name, line_number


def get_var_name_being_set_outside_of_pyquibbler() -> Optional[str]:
    """
    Get the current variable name being set outside of pyquibbler.
    If none is found, return None.
    This is not thread safe, as it keeps track_and_handle_new_graphics of the current line being accessed and which variable is being set in
    that line (eg a, b = iquib(1), iquib(2))
    """
    refnode = get_quib_node_being_set_outside_of_pyquibbler()
    if not refnode:
        return None
    node = find_relevant_parent_assignment_node(refnode)

    if not node:
        return None

    if isinstance(node, ast.Assign):
        # there could be a = b = iquib(1) -> in this case, we take the last
        target = node.targets[-1]
    else:
        target = node.target

    names = node_name(target)

    # node_name can return a list or a string depending on whether there were multiple assignments in the line
    if not isinstance(names, tuple):
        names = (names,)

    AST_ASSIGNMENTS_TO_VAR_NAME_STATES.setdefault(node, VarNameState(current_var_count=0, total_var_count=len(names)))
    var_name_state = AST_ASSIGNMENTS_TO_VAR_NAME_STATES.get(node)
    current_name = names[var_name_state.current_var_count]
    var_name_state.current_var_count += 1
    if var_name_state.current_var_count == var_name_state.total_var_count:
        AST_ASSIGNMENTS_TO_VAR_NAME_STATES.pop(node)

    return current_name
