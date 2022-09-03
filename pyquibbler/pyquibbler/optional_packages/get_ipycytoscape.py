from pyquibbler.optional_packages.emulate_missing_packages import EMULATE_MISSING_PACKAGES

PACKAGE_NAME = 'ipycytoscape'

if PACKAGE_NAME in EMULATE_MISSING_PACKAGES.val:
    raise ImportError

# noinspection PyPackageRequirements
import ipycytoscape  # noqa
