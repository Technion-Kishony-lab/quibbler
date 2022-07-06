Simple quib-app for probing image RGB
-------------------------------------

**A simple demo of a quib-based GUI.**

-  **Features**

   -  Graphics quibs
   -  Graphics-driven assignments
   -  Inverse assignments

-  **Try me**

   -  Try dragging the marker and see the RGB values of the image.

.. code:: python

    from pyquibbler import iquib, initialize_quibbler, q
    initialize_quibbler()
    import matplotlib.pyplot as plt
    import numpy as np
    %matplotlib tk

.. code:: python

    # Load and plot an image:
    file = iquib('bacteria_drop.tif')
    img = plt.imread(file)
    plt.figure(figsize=(8, 3))
    plt.subplot(1, 2, 1)
    plt.imshow(img)
    
    # Choose and plot an x-y point:
    xy = iquib([50, 45])
    x, y = xy
    plt.plot(x, y, 'w+', markersize=18, picker=True)
    plt.text(5, 10, xy, color='w', fontsize=14)
    
    # Plot the RGB at the chosen point:
    ax = plt.subplot(1, 2, 2)
    rgb = img[y, x, :]
    plt.bar(['R', 'G', 'B'], rgb, color=list('rgb'))
    ax.set_ylim([0, 255]);

.. image:: ../images/demo_gif/quibdemo_image_probing.gif
