Dragging whole object versus individual points
----------------------------------------------

**Moving a graphics object as a whole, or refining individual data
points.**

-  **Features:**

   -  Graphics-driven assignments
   -  Directing the path of inverse assignments
   -  Dragging invidual points versus whole object

-  **Try me:**

   -  Try dragging the ‘Move me!’ - it will move as a whole.
   -  Try dragging the ‘Change me!’ star - it will change individual
      points.

.. code:: python

    from pyquibbler import iquib, initialize_quibbler, q
    initialize_quibbler()
    import matplotlib.pyplot as plt
    import numpy as np
    %matplotlib tk

.. code:: python

    # Figure setup:
    fig1 = plt.figure(figsize=(4,4))
    ax = fig1.gca()
    ax.axis('square')
    ax.axis([0, 12, 0, 12]);

.. code:: python

    # Define star coordinates:
    nPoints = iquib(5)
    dtet = 2 * np.pi / (2*nPoints)
    tet = np.arange(np.pi/2, np.pi/2+2*np.pi, dtet)
    rR = np.array([1.5, 0.7])
    rs = np.tile(rR, (nPoints,))
    x_star = np.cos(tet) * rs
    y_star = np.sin(tet) * rs;

.. code:: python

    # Allow changing the coordinates:
    x_star.allow_overriding = True
    y_star.allow_overriding = True

.. code:: python

    # Close the shapes by connecting the last point to the first point
    x_star_circ = np.concatenate([x_star, x_star[[0]]])
    y_star_circ = np.concatenate([y_star, y_star[[0]]])

.. code:: python

    # Define and draw movable star:
    x_center_movable = iquib(7.)
    y_center_movable = iquib(5.)
    
    # using x_center_movable as the first argument in the summation 
    # (to which the inverse-assignment is channeled):
    x_movable_star = x_center_movable + x_star_circ
    y_movable_star = y_center_movable + y_star_circ
    ax.text(x_center_movable, y_center_movable + np.min(y_star_circ) - 0.2, 
            'Move me!', horizontalalignment='center', verticalalignment='top')
    ax.plot(x_movable_star, y_movable_star, linewidth=2, color='m', picker=True);

.. code:: python

    # Define and draw changeable star:
    x_center_fixed = iquib(2.)
    y_center_fixed = iquib(8.)
    
    # using x_star_circ as the first argument in the summation
    x_changeable_star = x_star_circ + x_center_fixed
    y_changeable_star = y_star_circ + y_center_fixed
    ax.text(x_center_fixed, y_center_fixed + np.min(y_star_circ) - 0.2, 
            'Change me!', horizontalalignment='center', verticalalignment='top')
    ax.plot(x_changeable_star, y_changeable_star, linewidth=2, color='c', picker=True);

.. code:: python

    ax.set_title(q('{:.1f},{:.1f}'.format, x_center_movable, y_center_movable));
.. image:: ../images/demo_gif/quibdemo_drag_whole_object_vs_individual_points.gif
