import matplotlib
from matplotlib import widgets, pyplot as plt

from pyquibbler import iquib
from pyquibbler.overriding.overriding import override_third_party_funcs

override_third_party_funcs()
matplotlib.use("TkAgg")
if __name__ == '__main__':
    actives = iquib([False, False, False])
    checkbox = widgets.CheckButtons(
        ax=plt.gca(),
        labels=['Red', 'Green', 'Blue'],
        actives=actives
    )

    plt.show()