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

# everything = np.concatenate((q(list, a), q(list, a2), q(list, b), q(list, b2), c, d))
# print(everything.get_value())
plt.plot(d, marker='o', markersize=18, picker=True, pickradius=20)
plt.show()
