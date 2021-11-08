import contextlib

from pyquibbler.env import SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.quib.function_quibs.exceptions import QuibCallFailedException


@contextlib.contextmanager
def quib_call_failed_exception_handling(quib):
    try:
        yield
    except Exception as e:
        if SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS:
            raise QuibCallFailedException(quibs=[quib], exception=e) from None
        raise

