import numpy as np
from matplotlib import pyplot as plt
from matplotlib import widgets
from pyquibbler import override_all, q

override_all()

h = 5
w = 5
plt.xlim(0, w)
plt.ylim(0, h)
ext = np.array([w // 2, w // 2 + 1, h // 2, h // 2 + 1], dtype=np.int32)
rois = 3
for x in range(rois):
    r = q(widgets.RectangleSelector, plt.gca(), extents=ext)
    plt.text(0, (x + 0.5) * h / rois, q(str, r.extents))
plt.show()
