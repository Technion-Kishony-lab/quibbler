import logging
from pathlib import Path

from pyquibbler.env import LOG_TO_STDOUT, LOG_TO_FILE

logger = logging.getLogger('pyquibblerLogger')
logger.setLevel(logging.ERROR)


if LOG_TO_STDOUT:
    logger.addHandler(logging.StreamHandler())

if LOG_TO_FILE:
    import __main__
    file = Path(__main__.__file__).parent / "pyquibbler.log"
    logger.addHandler(logging.FileHandler(file))
