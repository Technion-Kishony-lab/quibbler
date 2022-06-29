Quib-linked CheckButtons widget
-------------------------------

**A demo of interactive quib-linked matplotlib CheckButtons widget.**

-  **Features:**

   -  Quiby widgets.
   -  Quiby axis attributes.

-  **Try me:**

   -  Try playing with the check-buttons.

.. code:: python

    from pyquibbler import iquib, initialize_quibbler, q
    initialize_quibbler()
    import matplotlib.pyplot as plt
    from matplotlib import widgets
    %matplotlib tk

.. code:: python

    # Prepare figure, axes
    plt.figure(figsize=(3, 3))
    axs = plt.gca()

.. code:: python

    # Define input quib for colors:
    colors = iquib([False, True, True])

.. code:: python

    # Define a quib-widget
    # (Interaction with the widget changes the quib)
    widgets.CheckButtons(ax=axs, labels=['Red', 'Green', 'Blue'], actives=colors);

.. code:: python

    # Set the color of the axis to the quib colors
    axs.set_facecolor(colors);
.. image:: ../images/demo_gif/quibdemo_CheckButtons.gif
