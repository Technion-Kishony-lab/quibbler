import logging

from pyquibbler.env import LOG_TO_STDOUT, LOG_TO_FILE

logger = logging.getLogger('pyquibblerLogger')
logger.setLevel(logging.DEBUG)


if LOG_TO_STDOUT:
    logger.addHandler(logging.StreamHandler())

if LOG_TO_FILE:
    logger.addHandler(logging.FileHandler("/tmp/log.log"))
