import numpy as np

from pyquibbler import *
override_all()

parrots = iquib([3, 3, 4, 5])
print(f'i have {parrots}')

leg_count = (parrots[3] / 2) * 2

whatever = leg_count / 0

pasten = np.repeat([1, 2, 3], whatever)

to_fail = pasten[0] * 22

to_fail.get_value()




