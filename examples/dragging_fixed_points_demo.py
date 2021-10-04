import matplotlib.pyplot as plt
import numpy as np

from pyquibbler import iquib, override_all, q
from pyquibbler.quib.assignment import RangeAssignmentTemplate

override_all()

plt.figure(figsize=(10, 3))
plt.ylim([0, 1])
plt.xlim([0, 36.5])

x = iquib(2., assignment_template=RangeAssignmentTemplate(start=0, stop=6, step=1))
x_squared = x ** 2

bottom_x_options = np.array(range(0, 7)) ** 2
plt.plot(bottom_x_options, 0 * bottom_x_options, '.k', markersize=18)

plt.plot(x_squared, 0.1, marker='v', markerfacecolor='c', markersize=18, picker=True, pickradius=25)

plt.gca().set_xticks(bottom_x_options)
plt.gca().set_xticklabels(bottom_x_options, fontsize=18)
plt.gca().set_yticks([])

plt.title(q("Choose a square number: {:.0f}".format, x_squared))

plt.show()
