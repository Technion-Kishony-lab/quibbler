from typing import List

from pyquibbler.optional_packages.exceptions import PyQuibblerMissingPackageException
from pyquibbler.utilities.run_once import Mutable

EMULATE_MISSING_PACKAGES = Mutable([])


def get_packages(package_names: List[str], requested_for: str):
    missing_packages = []
    for package_name in package_names:
        try:
            if package_name in EMULATE_MISSING_PACKAGES.val:
                raise ImportError
            exec(f'import {package_name}')
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        raise PyQuibblerMissingPackageException(requested_for, missing_packages) from None

    return (eval(package_name) for package_name in package_names)


