Compare images
--------------

**Pairwise image comparison demosntrating diverged analysis.**

This analysis cuts *n* sub-images from a a source image based on user
specified Region of Interests (ROIs). Performs all pair-wise comparisons
and cluster images based on color similarity. When a single ROI changes
(is being dragged), quibbler knows to only make the calculation needed
to cut this specific image (see a single reporting of: “Cutting image”)
and re-performs the pairwise comparisons of this image with all others
(2 *n* - 1 recalculations. See reporting of”Comparing images”).

-  **Features**

   -  Diverged calculations of quib slices
   -  Calling user function with np.vectorize
   -  Graphics-driven assignments
   -  Inverse assignments
   -  Assignment template

-  **Try me**

   -  Drag the cyan diamond marker to choose a squared number.
   -  Drag the cyan square corner.

.. code:: python

    import numpy as np
    from functools import partial
    from matplotlib import pyplot as plt, widgets
    from mpl_toolkits.axes_grid1 import ImageGrid
    
    from pyquibbler import iquib, override_all, q
    from scipy.sparse.csgraph import connected_components
    override_all()
    
    %matplotlib tk

.. code:: python

    @partial(np.vectorize, signature='(4),()->()', pass_quibs=True, lazy=False)
    def create_roi(roi, axs):
        rectprops = dict(facecolor='k', edgecolor='k', alpha=0.2, fill=True)
        widgets.RectangleSelector(axs, extents=roi, rectprops=rectprops)
    
    
    @partial(np.vectorize, signature='(w,h,c),(4)->()',otypes=[object])
    def cut_image(image, roi):
        print("Cutting image")
        return image[roi[2]:roi[3], roi[0]:roi[1]]
    
    
    @partial(np.vectorize, otypes=[float])
    def image_distance(img1, img2):
        print("Comparing images")
        averages = np.average(img1, axis=(0, 1)) - np.average(img2, axis=(0, 1))
        return np.linalg.norm(averages) / np.linalg.norm(np.full(averages.shape, 255))
    
    
    @partial(np.vectorize,  signature='(),(4),()->()', lazy=False, otypes=[type(None)])
    def plot_roi_label(axs, roi, index):
        axs.text(roi[1], roi[2], chr(index+65), fontsize=20)

.. code:: python

    @partial(np.vectorize, lazy=False)
    def show_adjacency(axs, x, y, adjacent):
        symbol = 'x' if adjacent else '.'
        axs.plot(x, y, symbol, color='r')

.. code:: python

    # Read and draw source image
    file_name = iquib('../data_files/pipes.jpg')
    image = plt.imread(file_name)
    
    plt.figure(1, figsize=[10, 7])
    plt.imshow(image)
    ax1 = plt.gca()

.. code:: python

    images_count = iquib(6)
    images_count.set_assignment_template(0, 10, 1)
    
    roi_default = iquib([[20, 100, 20, 100]])
    roi_default.allow_overriding = False
    
    rois = np.repeat(roi_default, images_count, axis=0)
    rois.set_assignment_template(0, 1000, 1)
    rois.allow_overriding = True
    
    similiarity_threshold = iquib(np.array([.1]))

.. code:: python

    cut_images = cut_image(image, rois)


.. code:: python

    create_roi(rois, ax1)

.. code:: python

    widgets.Slider(
        ax=plt.axes([0.25, 0.1, 0.65, 0.03]),
        label=q("Similiarity threshold {:.1f}".format, similiarity_threshold[0]),
        valmin=0, valmax=1, valstep=.05,
        valinit=similiarity_threshold[0])
    
    widgets.Slider(
        ax=plt.axes([0.25, 0.05, 0.65, 0.03]),
        label=q("Image count ".format, images_count),
        valmin=1, valmax=9, valstep=1,
        valinit=images_count);

.. code:: python

    # Figure 2 - Plot images
    fig = plt.figure(2)
    grid_axes = iquib(ImageGrid(fig, 111, nrows_ncols=(3, 3), axes_pad=0.1))

.. code:: python

    np.vectorize(lambda ax, im: ax.imshow(im), signature='(),()->()', lazy=False)(
        grid_axes[:images_count], cut_images);

.. code:: python

    # Figure 3 - Compare sub images
    image_distances = image_distance(np.expand_dims(cut_images, 1), cut_images)
    adjacents = image_distances < similiarity_threshold

.. code:: python

    # Plot distance matrix
    fig = plt.figure(3)
    fig.clf()
    axs = fig.add_axes([0.1, 0.15, 0.7, 0.7])
    axs.imshow(1 - image_distances, cmap='gray', vmin=0, vmax=1)
    axs.axis([-0.5, images_count - 0.5, -0.5, images_count - 0.5])
    axs.set_title('pairwise distance between images')
    axs.set_xlabel('Image number')
    axs.set_ylabel('Image number')
    show_adjacency(axs, np.expand_dims(np.arange(images_count), 1), np.arange(images_count), adjacents);
    
    # colormap
    axclr = fig.add_axes([0.85, 0.15, 0.06, 0.7])
    clrmap = np.linspace(1,0,10).reshape(10,1)
    axclr.imshow(clrmap, cmap='gray', vmin=0, vmax=1)
    axclr.plot([-0.5,0.5], similiarity_threshold*10-0.5+np.array([0,0]), '-r', linewidth=4, picker=True)
    axclr.set_xticks([])
    axclr.set_yticks([])
    axclr.set_ylabel('Similarity Threshold')

.. code:: python

    # add cluster label
    rois.get_value()

.. code:: python

    c = q(connected_components,adjacents)[1]
    plot_roi_label(ax1, rois, c)
