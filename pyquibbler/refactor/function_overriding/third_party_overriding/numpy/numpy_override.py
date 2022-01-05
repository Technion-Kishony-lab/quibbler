import functools

import numpy as np

from pyquibbler.refactor.function_overriding.function_override import FunctionOverride

numpy_override = functools.partial(FunctionOverride.from_func, module_or_cls=np)
