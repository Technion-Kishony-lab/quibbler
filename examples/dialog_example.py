from pyquibbler import override_all, iquib
import matplotlib.pyplot as plt
import numpy as np
from pyquibbler import iquib, override_all
import matplotlib as mpl
from warnings import filterwarnings

filterwarnings('ignore')

override_all()
# %matplotlib widget
mpl.use('TkAgg')
plt.xlim(-5, 5)
plt.ylim(-5, 5)

a = iquib(np.array([0]))
a2 = a + 1
a2.allow_overriding = True

b = iquib(np.array([1]))
b2 = b - 1
b2.allow_overriding = True

c = np.concatenate((a2, b2))
c.allow_overriding = True

d = c + 1
d.allow_overriding = True

plt.plot(np.concatenate(([a], [a2], [b], [b2], c, d)), marker='o', markersize=18, picker=True, pickradius=20)
plt.show()
