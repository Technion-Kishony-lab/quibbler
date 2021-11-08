import numpy as np
from matplotlib import pyplot as plt
from matplotlib import widgets
from pyquibbler import override_all, q, iquib

override_all()

h = 5
w = 5
rois = 3
plt.xlim(0, w)
plt.ylim(0, h)
default_ext = iquib(np.array([w // 2, w // 2 + 1, h // 2, h // 2 + 1], dtype=np.int32))
default_ext._allow_overriding = False
exts = np.repeat([default_ext], rois, 0)
exts.set_allow_overriding(True)
for i, ext in enumerate(exts.iter_first(rois)):
    r = q(widgets.RectangleSelector, plt.gca(), extents=ext)
    plt.text(0, (i + 0.5) * h / rois, q(str, r.extents))
plt.show()
