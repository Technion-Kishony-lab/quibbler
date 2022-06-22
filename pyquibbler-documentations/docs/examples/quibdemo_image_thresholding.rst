Simple quib-app for image analysis
----------------------------------

**A simple demo of a quib-based GUI.**

-  **Features**

   -  Graphics quibs
   -  Graphics-driven assignments
   -  Inverse assignments

-  **Try me**

   -  Try dragging the RGB threshold values.

.. code:: python

    from pyquibbler import iquib, initialize_quibbler
    initialize_quibbler()

.. code:: python

    import matplotlib.pyplot as plt
    import numpy as np
    %matplotlib tk

.. code:: python

    # Load an image:
    filename = iquib('bacteria_drop.tif')
    img = plt.imread(filename)
    
    # Show the image:
    plt.figure()
    ax = plt.subplot(2, 2, 1)
    ax.imshow(img)
    
    # Threshold each of the RGB channels:
    thresholds_rgb = iquib(np.array([160, 170, 150]))
    img01 = img > np.reshape(thresholds_rgb,(1, 1, 3))
    
    # Plot the thresholded image:
    plt.subplot(2, 2, 3)
    plt.imshow(img01 * 1.)
    
    # Calculate fraction of area above threshold for each color:
    fraction_above_threshold = np.average(img01, (0, 1)) 
    
    # Plot detected areas:
    ax = plt.subplot(2, 2, 2)
    ax.bar([1, 2, 3], fraction_above_threshold * 100, color=list('rgb'))
    ax.axis([0.5, 3.5, 0, 1.5])
    
    # Plot the thresholds
    ax = plt.subplot(2, 2, 4)
    ax.axis([0.5, 3.5, 0, 255])
    ax.xaxis.grid(True)
    ax.plot([1, 2, 3], thresholds_rgb, 'sk', markersize=16, 
            markerfacecolor='k', picker=True);

.. code:: python

    # Show thresholds on log scale:
    log_thresholds_rgb = np.log2(thresholds_rgb)
    
    fg = plt.figure(figsize=(4, 3))
    ax = fg.gca()
    ax.plot([1, 2, 3], log_thresholds_rgb, 'sk', markersize=16, markerfacecolor='k', picker=True)
    ax.axis([0.5, 3.5, 0, 8])
    ax.xaxis.grid(True)
    ax.set_xticks([1, 2, 3]);
