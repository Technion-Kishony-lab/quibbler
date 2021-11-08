from __future__ import annotations
import contextlib
import functools
from typing import TYPE_CHECKING

from pyquibbler.env import SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.exceptions import PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class QuibCallFailedException(PyQuibblerException):

    def __init__(self, quibs, exception):
        self.quibs = quibs
        self.exception = exception

    def __str__(self):
        quib_reprs = list(map(repr, self.quibs))
        quibs_formatted = ""
        indent_level = "  "
        for quib_repr in quib_reprs[::-1]:
            quibs_formatted += "\n" + indent_level + quib_repr
            indent_level += "  "
        last_quib = self.quibs[-1]
        return f"Failed to execute {last_quib}, " \
               f"the following quibs were in the stack of the exception: {quibs_formatted} " \
               f"failed with:\n{type(self.exception).__name__}: {self.exception}"


@contextlib.contextmanager
def quib_call_failed_exception_handling(quib: Quib):
    """
    Use this context manager whenever running a quib's function that can fail user-wise
    (for example, whenever calling a np func or a user func)
    This should not be used around functions that can fail because pyquibbler internals themselves failed
    """
    try:
        yield
    except Exception as e:
        if SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS:
            raise QuibCallFailedException(quibs=[quib], exception=e) from None
        raise


def raise_quib_call_exceptions_as_own(func):
    """
    Raise any quib call failed exceptions as though they were your own (so as to prevent long tracebacks)
    """
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QuibCallFailedException as e:
            # We do this to clear the get_value_valid_at_path from traceback
            raise QuibCallFailedException(exception=e.exception, quibs=e.quibs) from None

    return _wrapper
