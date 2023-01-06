from pyquibbler.utilities.basic_types import Flag
from pyquibbler.utilities.warning_messages import no_header_warn

IS_QUIBBLER_INITIATED = Flag(False)


def set_quibbler_initialized(value: bool = True):
    IS_QUIBBLER_INITIATED.val = value


def is_quibbler_initialized():
    return IS_QUIBBLER_INITIATED.val


def warn_if_quibbler_not_initialized(message: str = ''):
    if not is_quibbler_initialized():
        no_header_warn(message + 'WARNING:\n'
                                 'Quibbler has not been initialized.\n'
                                 'Your code will run without quibs.\n'
                                 'To initiate Quibbler, run initialize_quibbler()\n',
                       once_only=True)
