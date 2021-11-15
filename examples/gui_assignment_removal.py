from matplotlib import pyplot as plt
from pyquibbler import iquib, override_all, q

override_all()

plt.title('Move the dots around and then right click them')
plt.plot(iquib([0, 1, 2]), iquib([0, 1, 2]), marker='o', markersize=9, linestyle='None', picker=True)
plt.show()
