from pyquibbler import iquib, override_all, q
override_all()
import matplotlib.pyplot as plt
import numpy as np


# define and plot a curve:
curve_function = lambda v: 4 * v ** 2 - v ** 3
graph_xs = np.arange(0, 4, .2)
graph_ys = curve_function(graph_xs)
plt.figure(figsize=(4,3))
plt.plot(graph_xs, graph_ys, 'k')
plt.axis([0, 4, 0, 12])

# define x-y quibs:
point_x = iquib(3.)
point_y = q(curve_function, point_x)

# Plot the point, use picker=True to allow dragging
plt.plot(point_x, point_y, marker='o', markerfacecolor='c',
         markersize=18, picker=True, pickradius=20)

# Define and plot text (this text will change when the marker is dragged):
xy_str = q("X={:.2f}, Y={:.2f}".format, point_x, point_y)
plt.text(point_x, point_y + .6, xy_str,
         horizontalalignment="center",
         verticalalignment="bottom", fontsize=13)


plt.show()
