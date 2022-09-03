from __future__ import annotations

import contextlib
import functools
import sys
import traceback

from varname.utils import cached_getmodule

from pyquibbler.env import SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.exceptions import PyQuibblerException


def get_user_friendly_name_for_requested_evaluation(func, args, kwargs):
    """
    Get a user-friendly name representing the call to get_value_valid_at_path
    """
    func_name = func.__name__
    if func_name != 'get_value_valid_at_path':
        return func_name + '()'
    valid_path = args[1] if len(args) > 0 else kwargs.get('path')
    if valid_path is None:
        return 'get_blank_value()'
    elif len(valid_path) == 0:
        return 'get_value()'
    else:
        return f'get_value_valid_at_path({valid_path})'


class ExternalCallFailedException(PyQuibblerException):

    def __init__(self, quibs_with_calls, exception, tb):
        self.quibs_with_calls = quibs_with_calls
        self.exception = exception
        self.traceback = tb

    def __str__(self):
        if len(self.quibs_with_calls) == 0:
            return ''

        quibs_formatted = ""
        for quib, call in self.quibs_with_calls[::-1]:
            file_info = f"File \"{quib.created_in.file_path}\", line {quib.created_in.line_no}" \
                if quib.created_in else "Untraceable quib"
            quibs_formatted += "\n  " + file_info
            quibs_formatted += f"\n\t{repr(quib)} -> {call} "

        last_quib, _ = self.quibs_with_calls[-1]
        return f"Failed to execute {last_quib}\n\n" \
               f"The following quibs were in the stack of the exception: {quibs_formatted} " \
               f"\n\n{self.traceback}"


@contextlib.contextmanager
def external_call_failed_exception_handling():
    """
    Use this context manager whenever running a quib's function that can fail user-wise
    (for example, whenever calling a np func or a user func)
    This should not be used around functions that can fail because pyquibbler internals themselves failed
    """
    try:
        yield
    except Exception as e:
        if not SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS:
            raise

        # get traceback outside of pyquibbler
        type_, exc, tb = sys.exc_info()
        while tb is not None and cached_getmodule(tb.tb_frame.f_code) is not None \
                and cached_getmodule(tb.tb_frame.f_code).__name__.startswith("pyquibbler"):
            tb = tb.tb_next

        if tb is None:
            formatted_tb = ''.join(traceback.format_exception_only(type_, value=exc))
        else:
            formatted_tb = ''.join(traceback.format_exception(type_, exc, tb))

        raise ExternalCallFailedException(quibs_with_calls=[],
                                          exception=e,
                                          tb=formatted_tb) from None


def raise_quib_call_exceptions_as_own(func):
    """
    Raise any quib call failed exceptions as though they were your own (so as to prevent long tracebacks)
    """
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ExternalCallFailedException as e:
            # We want to remove any context
            quib = args[0]
            new_quib_with_call = (quib, get_user_friendly_name_for_requested_evaluation(func, args, kwargs))
            quibs_with_calls = e.quibs_with_calls
            exc = ExternalCallFailedException(exception=e.exception,
                                              quibs_with_calls=[*quibs_with_calls, new_quib_with_call],
                                              tb=e.traceback)
            raise exc from None

    return _wrapper
