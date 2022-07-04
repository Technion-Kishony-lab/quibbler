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

    plt.figure(1, figsize=(8, 3));
    plt.clf()

.. code:: python

    # Load and plot an image:
    file = iquib('bacteria_drop.tif')
    img = plt.imread(file)
    plt.subplot(1, 2, 1)
    plt.imshow(img)
    
    # Choose and plot an x-y point:
    xy = iquib(np.array([50, 45]))
    plt.plot(xy[0], xy[1], 'w+', markersize=18, picker=True)
    plt.text(5, 10, np.array2string(xy), color='w', fontsize=14)
    
    # Plot the RGB at the chosen point:
    ax = plt.subplot(1, 2, 2)
    rgb = img[xy[1], xy[0], :]
    plt.bar([0, 1, 2], rgb, color=['r', 'g', 'b'])
    plt.setp(ax, xticks=[0, 1, 2], xticklabels=rgb, ylim=[0, 255]);

.. image:: ../images/demo_gif/quibdemo_image_probing.gif
