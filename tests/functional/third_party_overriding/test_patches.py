from


def test_axes_add_patch_on_non_quib(axes):
    axes.


from pyquibbler import iquib, initialize_quibbler
initialize_quibbler()

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import matplotlib
matplotlib.use("TkAgg")

fig = plt.figure()
ax = plt.gca()
ax.axis([0, 10, 0, 10])
w = iquib(2)
# w = 2
r1 = Rectangle((1, 1), w, 6)
ax.add_patch(r1)

w.assign(3)

plt.show()
