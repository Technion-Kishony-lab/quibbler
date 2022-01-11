import matplotlib
from matplotlib import widgets, pyplot as plt

from pyquibbler import iquib
from pyquibbler.refactor.function_definitions import override_all

override_all()
matplotlib.use("TkAgg")
if __name__ == '__main__':
    actives = iquib([False, False, False])
    checkbox = widgets.CheckButtons(
        ax=plt.gca(),
        labels=['Red', 'Green', 'Blue'],
        actives=actives
    )

    plt.show()