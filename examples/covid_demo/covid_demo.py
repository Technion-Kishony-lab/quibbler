from matplotlib import pyplot as plt

from pyquibbler import iquib, q, override_all
import numpy as np


override_all()


file_name = iquib('COVID_Fatality.csv')

fatality_table = np.genfromtxt(file_name, dtype=[("Country", str, 32), ("ConfirmedCases", int),
                                                            ("Deaths", int),  ("Population", float)
                                                            ], delimiter=',', names=True)

rate = fatality_table['ConfirmedCases'] / fatality_table['Population'] * 100

plt.xlabel("Confirmed Cases (%)")
plt.ylabel("Number of countries")
plt.xlim([0, 20])
plt.hist(rate, np.arange(0, 20, 1), facecolor='g', edgecolor='black', linewidth=1.2)


threshold = iquib(15)
below_threshold = rate < threshold
above_threshold = rate >= threshold

plt.hist(rate[above_threshold], np.arange(0, 20, 1), facecolor='r', alpha=1, edgecolor='black', linewidth=1.2)
plt.plot(threshold, 0, markerfacecolor='k', marker='^', markersize=30, picker=True, pickradius=30)

plt.text(18, 68, 'High-rate countries', fontsize=14, verticalalignment='top',
         horizontalalignment='right', color='r')
plt.text(18, 63, q("\n".join, fatality_table[above_threshold]['Country']), verticalalignment='top',
         horizontalalignment='right', color='r')


below_threshold_sum = q(sum, below_threshold)
above_threshold_sum = q(sum, above_threshold)
ax = plt.axes([0.3, 0.4, 0.3, 0.3])
plt.pie([below_threshold_sum, above_threshold_sum], colors=['g', 'r'])

plt.show()
