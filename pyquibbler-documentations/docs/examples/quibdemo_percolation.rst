Random simulations of lattice percolation
-----------------------------------------

**A simple demo of a quib-based GUI for lattice percolation.**

-  **Features**

   -  User-defined functions
   -  Random quibs
   -  Graphics-driven assignments

-  **Try me**

   -  Try adjusting the lattice density. Note the size of the largest
      cluster (in gray).

.. code:: python

    from pyquibbler import iquib, initialize_quibbler, quiby, reset_random_quibs
    initialize_quibbler()
    
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.widgets import Slider, Button
    from matplotlib.cm import get_cmap
    from matplotlib.colors import ListedColormap
    from scipy.ndimage import label
    %matplotlib tk

.. code:: python

    @quiby
    def get_connected_components(img):
        clusters, num_clusters = label(img)
        cluster_sizes, _ = np.histogram(clusters, np.arange(1, num_clusters + 2))
        largest_cluster = np.argmax(cluster_sizes) + 1
        cmp = get_cmap('rainbow', num_clusters + 1)
        cmp = cmp(np.arange(num_clusters + 1))
        cmp[0, :3] = 0
        cmp[largest_cluster, :3] = 0.7
        return clusters, ListedColormap(cmp)

.. code:: python

    # Set quibs
    density = iquib(0.6)
    size = iquib(200)
    lattice = np.random.rand(size, size) < density
    clusters, cmp = get_connected_components(lattice)
    
    fig = plt.figure(figsize=(8, 8))
    plt.imshow(clusters, cmap=cmp)
    plt.axis('off');

.. code:: python

    # Slider for the density value
    ax = fig.add_axes([0.3, 0.06, 0.4, 0.02])
    Slider(ax, label='density = ', valmin=0, valmax=1, valinit=density);

.. code:: python

    # Randomization button
    ax = fig.add_axes([0.75, 0.02, 0.2, 0.03])
    randomize_button = Button(ax, label='Randomize')
    randomize_button.on_clicked(lambda x: reset_random_quibs());
.. image:: ../images/demo_gif/quibdemo_percolation.gif
