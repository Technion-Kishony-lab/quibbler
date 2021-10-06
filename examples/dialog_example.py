import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from pyquibbler import override_all, iquib

override_all()

plt.xlim(-1, 9)
plt.ylim(-1, 7)

a = iquib(np.array([0]))
a2 = a + 1
a2.allow_overriding = True

b = iquib(np.array([1]))
b2 = b * 2
b2.allow_overriding = True

c = b2 + 1

e = a2[0] + b2[0]
e.allow_overriding = True
# TODO: 1. dragging goes to opposite side 2. when there is dependent, we change the left quib

# allz = (q(np.array, a), q(np.array, a2), q(np.array, b), q(np.array, b2), c, d, q(np.array, [e]))
# print([a.get_value() for a in allz])
# everything = np.concatenate(allz)
# print(everything.get_value())
plt.plot(e, marker='o', markersize=18, picker=True, pickradius=20)
plt.show()
