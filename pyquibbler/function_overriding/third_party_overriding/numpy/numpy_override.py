import functools

import numpy as np

from pyquibbler.function_overriding.function_override import FuncOverride

numpy_override = functools.partial(FuncOverride.from_func, module_or_cls=np)
