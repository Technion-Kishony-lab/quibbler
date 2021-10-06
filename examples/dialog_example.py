import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from pyquibbler import override_all, iquib, q

override_all()
mpl.use('TkAgg')

plt.xlim(-1, 8)
plt.ylim(-1, 7)

a = iquib(np.array([0]))
a2 = a + 1
a2.allow_overriding = True

b = iquib(np.array([1]))
b2 = b * 2
b2.allow_overriding = True

c = np.concatenate((a2, b2))
c.allow_overriding = True

d = c + 1
d.allow_overriding = True

allz = (c, d)  # (q(np.array, a), q(np.array, a2), q(np.array, b), q(np.array, b2), c, d)
print([a.get_value() for a in allz])
everything = np.concatenate(allz)
print(everything.get_value())
plt.plot(everything, marker='o', markersize=18, picker=True, pickradius=20)
plt.show()
