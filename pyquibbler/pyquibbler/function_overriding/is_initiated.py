from pyquibbler.utilities.basic_types import Flag
from pyquibbler.utilities.warning_messages import no_header_warn

IS_QUIBBLER_INITIATED = Flag(False)


def is_quibbler_initiated():
    return IS_QUIBBLER_INITIATED.val


def warn_if_quibbler_not_initiated(message: str = ''):
    if not is_quibbler_initiated():
        no_header_warn(message + 'WARNING: Quibbler is not yet initiated.\nNeed to run initiate_quibbler()',
                       once_only=True)
