# THIS DEMO DOES NOT WORK 100%

import numpy as np
from matplotlib import pyplot as plt, widgets
from mpl_toolkits.axes_grid1 import ImageGrid

from pyquibbler import iquib, override_all, q, quibbler_user_function

override_all()


def create_roi(roi, axes):
    widgets.RectangleSelector(axes, extents=roi)


def cut_image(roi):
    im = image[roi[2]:roi[3], roi[0]:roi[1]]
    return im


@quibbler_user_function()
def image_distance(img1, img2):
    return np.average(img1) - np.average(img2)


file_name = iquib('/Users/maor/Documents/pyquibbler/examples/compare_images/pipes.jpg')
image = plt.imread(file_name)

images_count = iquib(6)
images_count.set_assignment_template(0, 10, 1)

roi_default = iquib([[10, 110, 10, 110]])
roi_default.allow_overriding = False

rois = np.repeat(roi_default, images_count, axis=0)
rois.set_assignment_template(0, 1000, 1)
rois.allow_overriding = True

rois_itered = list(rois.iter_first(images_count.get_value()))

similiarity_threshold = iquib(.1)


def create_figure_1():
    plt.figure(1, figsize=[10, 7])
    plt.axes([.1, .2, .8, .7])
    plt.imshow(image, aspect="auto")

    for roi in rois_itered:
        create_roi(roi, plt.gca())

    axfreq = plt.axes([0.25, 0.1, 0.65, 0.03])
    widgets.Slider(
        ax=axfreq,
        label=q("Similiarity threshold {:.1f}".format, similiarity_threshold),
        valmin=.1,
        valmax=1,
        valstep=.1,
        valinit=similiarity_threshold
    )

    axfreq = plt.axes([0.25, 0.05, 0.65, 0.03])
    widgets.Slider(
        ax=axfreq,
        label=q("Image count ".format, images_count),
        valmin=1,
        valmax=6,
        valstep=.1,
        valinit=images_count
    )


create_figure_1()


cut_images_lst = [cut_image(roi) for roi in rois_itered]


# Plot images
fig = plt.figure(2)
grid = ImageGrid(fig, 111,  # similar to subplot(111)
                 nrows_ncols=(3, 3),  # creates 2x2 grid of axes
                 axes_pad=0.1,  # pad between axes in inch.
                 )

for ax, im in zip(grid, cut_images_lst):
    # Iterating over the grid returns the Axes.
    ax.imshow(im)


# Compare sub images
image_distances = np.array([[image_distance(img1, img2) for img2 in cut_images_lst] for img1 in cut_images_lst])
adjacents = image_distances < similiarity_threshold



# Plot distance matrix
plt.figure(3)
plt.axis([0.5, images_count+0.5, 0.5, images_count+0.5 ])
plt.title('pairwise distance between images')
plt.xlabel('Image number')
plt.ylabel('Image number')


#
for i in range(1, images_count.get_value() + 1):
    adjacents_for_image = adjacents[i - 1]
    ss = [(adjacents_for_image[i] * 100 + 1) for i in range(images_count.get_value())]
    plt.scatter(list(range(1, images_count.get_value() + 1)), np.repeat([i], images_count),
                s=ss,
                marker='x',
                color='r',
                linewidths=2)

plt.show(block=True)
