import numpy as np
from matplotlib import pyplot as plt

from pyquibbler import iquib, override_all, q

override_all()


def curve_function(v):
    return 4 * v ** 2 - v ** 3


point_x = iquib(3)
point_y = curve_function(point_x)

graph_xs = np.arange(0, 4, .2)
graph_ys = curve_function(graph_xs)

plt.xlim(0, max(graph_xs))
plt.ylim(0, max(graph_ys) + 2)

# Create a line representing graph
plt.plot(graph_xs, graph_ys, 'k')

# Plot the point and the text
plt.plot(point_x, point_y, marker='o', markerfacecolor='c', markersize=18, picker=True, pickradius=20)
plt.text(point_x, point_y + .6, q("X={:.2f}, Y={:.2f}".format, point_x, point_y), horizontalalignment="center",
         verticalalignment="bottom", fontsize=13)

plt.show()
