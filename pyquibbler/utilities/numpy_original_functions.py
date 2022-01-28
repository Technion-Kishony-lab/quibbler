import numpy as np
from pyquibbler.quib.factory import get_original_func

np_logical_and = get_original_func(np.logical_and)
np_logical_or = get_original_func(np.logical_or)
np_ndarray = get_original_func(np.ndarray)
