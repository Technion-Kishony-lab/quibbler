import ast
from dataclasses import dataclass
from typing import Optional

from varname.utils import ASSIGN_TYPES, get_node, node_name, AssignType

from pyquibbler.exceptions import PyQuibblerException


class CannotFindNodeException(PyQuibblerException):
    pass


@dataclass
class VarNameState:
    total_var_count: int
    current_var_count: int


var_name_state = None


def lookfor_parent_assign(node: ast.AST) -> AssignType:
    """Look for an ast.Assign node in the parents"""
    if hasattr(node, 'parent'):
        node = node.parent
        if isinstance(node, ASSIGN_TYPES):
            return node
        if isinstance(node, ast.Tuple) and hasattr(node, 'parent') and isinstance(node.parent, ASSIGN_TYPES):
            return node.parent
    return None


def get_var_name_being_set_outside_of_pyquibbler() -> Optional[str]:
    """
    Get the current variable name being set outside of pyquibbler.
    If none is found, return None.
    This is not thread safe, as it keeps track of the current line being accessed and which variable is being set in
    that line (eg a, b = iquib(1), iquib(2))
    """
    global var_name_state

    import pyquibbler
    refnode = get_node(frame=1, ignore=pyquibbler, raise_exc=False)
    if not refnode:
        return None
    node = lookfor_parent_assign(refnode)
    if not node:
        return None

    if isinstance(node, ast.Assign):
        target = node.targets[-1]
    else:
        target = node.target

    names = node_name(target)

    if not isinstance(names, tuple):
        names = (names,)

    if var_name_state is None:
        var_name_state = VarNameState(
            current_var_count=0,
            total_var_count=len(names)
        )

    current_name = names[var_name_state.current_var_count]
    var_name_state.current_var_count += 1
    if var_name_state.current_var_count == var_name_state.total_var_count:
        var_name_state = None

    return current_name
