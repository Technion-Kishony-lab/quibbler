import numpy as np
from matplotlib import pyplot as plt

from pyquibbler import iquib, override_all, q

override_all()

x = iquib(7)
y = iquib(4)

plt.xlim(0, 10)
plt.ylim(0, 10)

# Lines connecting dot to axeses
plt.plot([x, x], [0, y], color='k', linewidth=2, linestyle=':')
plt.plot([0, x], [y, y], color='r', linewidth=2, linestyle=':')

# Text above dot
plt.text(x, y + 0.6, q("({}, {})".format, np.around(x, decimals=2), np.around(y, decimals=2)),
         horizontalalignment="center",
         verticalalignment="bottom", fontsize=16)

# Vertical and horizontal sliders
plt.plot(x, 0, '^', markerfacecolor='r', markersize=18, picker=True)
plt.plot(0, y, '>', markerfacecolor='r', markersize=18, picker=True)


# Draggable dot
plt.plot(x, y, markerfacecolor='red', marker='o', markersize=25, picker=True, pickradius=25)

plt.show()
