import logging

from pyquibbler.env import LOG_TO_STDOUT

logger = logging.getLogger('pyquibblerLogger')
logger.setLevel(logging.DEBUG)


if LOG_TO_STDOUT:
    logger.addHandler(logging.StreamHandler())
