from pyquibbler import iquib, override_all, q
override_all()
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import numpy as np
import os

plt.figure()

# Load and plot an image:
axs1 = plt.gca()
filename = iquib(os.path.join('..','data_files','bacteria_in_droplets.tif'))
img = plt.imread(filename)
axs1.imshow(img)

# Define and plot rectangle ROI
ROI = iquib(np.array([236, 336, 362, 462]))

RectangleSelector(axs1, extents=ROI, rectprops=dict(edgecolor='w', alpha=0.7, fill=False, linewidth=3))

# Extract and plot the ROI from the main image:
img_cut = q(lambda im,roi: im[roi[2]:roi[3],roi[0]:roi[1],:],img,ROI)

fig = plt.figure()
axs2 = fig.add_axes([0.1,0.1,0.3,0.8])
axs2.imshow(img_cut)
axs2.set_xticks([])
axs2.set_yticks([])

# Add a rectangle ROI around the extracted image:
# RectangleSelector(axs2, extents=ROI-ROI[[0,0,2,2]], rectprops=dict(edgecolor='black', alpha=0.7, fill=False, linewidth=3))

# Do some downstream analysis on the ROI:
thresholds = iquib(np.array([160,170,150]).reshape(1,1,3))
avgRGB = np.average(img_cut>thresholds, (0,1))
axs3 = fig.add_axes([0.6,0.1,0.3,0.8])
plt.bar([1,2,3],avgRGB*100,color=['r','g','b'])
axs3.set_ylim([0,1.5])
axs3.set_ylabel('Total detected area, %')
axs3.set_xticks([1,2,3])
axs3.set_xticklabels(['Red','Green','Blue'])

plt.show()