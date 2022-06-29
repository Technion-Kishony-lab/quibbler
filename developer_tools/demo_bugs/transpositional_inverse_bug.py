import numpy as np
from pyquibbler import initialize_quibbler, q, iquib

initialize_quibbler()

a = iquib(np.array([1, 2, 3, 4]))
b = np.repeat([a], 3, 0)

np.repeat([a.get_value()], 3, 0),  "sanity"

b.get_value()

