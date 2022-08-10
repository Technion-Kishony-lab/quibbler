from contextlib import contextmanager
from typing import Optional

GET_VALUE_CONTEXT_PASS_QUIBS: Optional[bool] = None


@contextmanager
def get_value_context(pass_quibs: bool = False):
    """
    Change IS_WITHIN_GET_VALUE_CONTEXT while in the process of running get_value.
    This has to be a static method as the IS_WITHIN_GET_VALUE_CONTEXT is a global state for all quib types
    """
    global GET_VALUE_CONTEXT_PASS_QUIBS
    if GET_VALUE_CONTEXT_PASS_QUIBS is not None:
        yield
    else:
        GET_VALUE_CONTEXT_PASS_QUIBS = pass_quibs
        try:
            yield
        finally:
            GET_VALUE_CONTEXT_PASS_QUIBS = None


def is_within_get_value_context() -> bool:
    return GET_VALUE_CONTEXT_PASS_QUIBS is not None


def get_value_context_pass_quibs() -> Optional[bool]:
    return GET_VALUE_CONTEXT_PASS_QUIBS
