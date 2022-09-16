import sys
import logging
from typing import Optional, Callable

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.get_value_context_manager import is_within_get_value_context
from pyquibbler.utilities.warning_messages import no_header_warn

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

original_showtraceback: Optional[Callable] = None

QUIBY_WARNING_MESSAGE = (
        'It seems that a quib has been used in a regular, non-quiby, function.',
        'To see a list of all quiby functions, use:  list_quiby_funcs()',
        'To check if a given function is quiby, use: is_quiby(func)',
        '',
        'Note that any function, even if not quiby, can still be implemented',
        'with quibs, using either:',
        '                           quiby(func)(quib1, quib2, ...)',
        '                           q(func, quib1, quib2, ...)',
)


def handle_exception(exc_type, exc_value, exc_traceback):
    original_showtraceback(exc_type, exc_value, exc_traceback)

    if issubclass(exc_type, KeyboardInterrupt):
        return

    if issubclass(exc_type, PyQuibblerException) or is_within_get_value_context():
        return

    if 'Quib' in str(exc_value) or 'Quib' in str(exc_type) or \
            len(exc_traceback) > 0 and 'Quib' in str(exc_traceback[-1]):
        print()
        no_header_warn(QUIBY_WARNING_MESSAGE, add_frame=True)


def override_jupyterlab_excepthook():
    global original_showtraceback
    from pyquibbler.optional_packages.get_IPython import get_ipython

    ipython = get_ipython()
    original_showtraceback = ipython._showtraceback

    ipython._showtraceback = handle_exception
