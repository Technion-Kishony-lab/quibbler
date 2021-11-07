# THIS DEMO DOES NOT WORK 100%
import weakref
import numpy as np
from functools import partial

from matplotlib import pyplot as plt, widgets
from matplotlib.widgets import AxesWidget
from mpl_toolkits.axes_grid1 import ImageGrid

from pyquibbler import iquib, override_all, q

override_all()


@partial(np.vectorize, signature='(extents),()->()', pass_quibs=True)
def create_roi(roi, axes):
    print("Creating ROI")
    widgets.RectangleSelector(axes, extents=roi, allow_resize=False)


@partial(np.vectorize, signature='(w,h,c),(extents)->(w2,h2,c)')
def cut_image(image, roi):
    print("Cutting image")
    return image[roi[2]:roi[3], roi[0]:roi[1]]


@partial(np.vectorize, signature='(w,h,c),(w,h,c)->()')
def image_distance(img1, img2):
    print("Comparing images")
    return np.linalg.norm(np.average(img1, axis=(0, 1)) - np.average(img2, axis=(0, 1))) / 255


@np.vectorize
def show_adjacency(axes, x, y, adjacent):
    axes.scatter(x, y,
                 s=adjacent * 100 + 1,
                 marker='x',
                 color='r',
                 linewidths=2)


file_name = iquib('./pipes.jpg')
image = plt.imread(file_name)

images_count = iquib(3)
images_count.set_assignment_template(0, 10, 1)

roi_default = iquib([[10, 110, 10, 110]])
roi_default.allow_overriding = False

rois = np.repeat(roi_default, images_count, axis=0)
rois.set_assignment_template(0, 1000, 1)
rois.allow_overriding = True

similiarity_threshold = iquib(.1)
cut_images = cut_image(image, rois)


def create_figure_1():
    plt.figure(1, figsize=[10, 7])
    plt.axes([.1, .2, .8, .7])
    plt.imshow(image, aspect="auto")

    create_roi(rois, plt.gca())

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
        valmax=9,
        valstep=1,
        valinit=images_count
    )


def create_figure_2():
    # Plot images
    fig = plt.figure(2)
    grid_axes = iquib(np.array(list(ImageGrid(fig, 111,
                                              nrows_ncols=(3, 3),
                                              axes_pad=0.1,
                                              ))))

    np.vectorize(lambda ax, im: ax.imshow(im), signature='(),(w,h,c)->()')(grid_axes[:q(int, images_count)], cut_images)


def create_figure_3():
    # Compare sub images
    image_distances = image_distance(np.expand_dims(cut_images, 1), cut_images)
    adjacents = image_distances < similiarity_threshold

    # Plot distance matrix
    plt.figure(3)
    plt.axis([-0.5, images_count - 0.5, -0.5, images_count - 0.5])
    plt.title('pairwise distance between images')
    plt.xlabel('Image number')
    plt.ylabel('Image number')

    show_adjacency(plt.gca(), np.expand_dims(np.arange(images_count), 1), np.arange(images_count), adjacents)


create_figure_1()
create_figure_2()
create_figure_3()

plt.show(block=True)
