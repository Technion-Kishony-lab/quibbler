Dragging graphics vertically/horizontally
=========================================

**A demo of interactive graphics-driven assignments with
vertical/horizontal dragging.**

-  **Features**

   -  Graphics-driven assignments
   -  Horizontal/vertical dragging
   -  Inverse assignments

-  **Try me**

   -  Try dragging the corners
   -  Try dragging the edges

.. code:: python

    from pyquibbler import iquib, initialize_quibbler, q
    initialize_quibbler()
    import matplotlib.pyplot as plt
    import numpy as np
    %matplotlib tk

.. code:: python

    # Figure setup and graphic properties
    plt.figure(figsize=(4, 4))
    plt.axis('square')
    plt.axis([-4, 10, -1, 11])
    
    # Define x-y coordinates
    x0 = iquib(0.)
    x1 = iquib(6.)
    x2 = iquib(6.)
    y = 8.
    
    # Plot parallelogram
    plt.plot([x0, x2 - x1 + x0, x2 + x0, x1 + x0, x0], [0, y, y, 0, 0], 'k:D', linewidth=2);


