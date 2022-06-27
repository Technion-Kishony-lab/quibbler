import numpy as np
from pyquibbler import override_all, q, iquib

override_all()

a = iquib(np.array([1, 2, 3, 4]))
b = np.repeat([a], 3, 0)

np.repeat([a.get_value()], 3, 0),  "sanity"

b.get_value()

