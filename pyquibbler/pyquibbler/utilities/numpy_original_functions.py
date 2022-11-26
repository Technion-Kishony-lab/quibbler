import numpy as np

from pyquibbler.utilities.get_original_func import get_original_func

np_logical_and = get_original_func(np.logical_and)
np_logical_or = get_original_func(np.logical_or)
np_cumsum = get_original_func(np.cumsum)
np_sum = get_original_func(np.sum)
np_all = get_original_func(np.all)
np_any = get_original_func(np.any)
np_full = get_original_func(np.full)
np_ndarray = get_original_func(np.ndarray)
np_array = get_original_func(np.array)
np_log10 = get_original_func(np.log10)
np_abs = get_original_func(np.abs)
np_vectorize = get_original_func(np.vectorize)
np_maximum = get_original_func(np.maximum)
np_minimum = get_original_func(np.minimum)
np_round = get_original_func(np.round)
np_zeros = get_original_func(np.zeros)
np_True = np.bool_(True)
np_shape = get_original_func(np.shape)
