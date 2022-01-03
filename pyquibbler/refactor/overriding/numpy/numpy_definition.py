import functools

import numpy as np

from pyquibbler.refactor.overriding.override_definition import OverrideDefinition

numpy_definition = functools.partial(OverrideDefinition.from_func, module_or_cls=np)
