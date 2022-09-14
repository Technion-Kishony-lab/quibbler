from pyquibbler.optional_packages.emulate_missing_packages import EMULATE_MISSING_PACKAGES

PACKAGE_NAME = 'IPython'

if PACKAGE_NAME in EMULATE_MISSING_PACKAGES.val:
    raise ImportError

from IPython.display import display, HTML  # noqa: F401, E402
from IPython import get_ipython  # noqa: F401, E402

# noinspection PyPackageRequirements
from ipykernel.comm import Comm  # noqa: F401, E402
