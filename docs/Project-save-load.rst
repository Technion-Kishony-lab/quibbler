Project save/load
-----------------

WIP
^^^

*Quibbler* allows saving and loading the value of input quibs as well as
overriding, if any, to function quibs.

A quib can be bi-directionally connected with a linked input file (LIF),
where inputs to the quib are saved. LIFs can be saved in simple text
human readable/writable files, providing a transparent record of user
defined parameters and changes. The linkage between a quib and its LIF
is bidirectional - changes to the inputs of the quib can update the
file, and changes to the file can update the quib.

There are two types of LIFs:

-  Array linked input file (arr-LIF): For an i-quib, the linked input
   file saves the whole array represented by the i-quib.

-  Overriding linked input file (ovr-LIF): For a functional quib, the
   linked input file saves the list of any user overrides to the quib.

Import
~~~~~~

.. code:: python

    # Quibbler import:
    import pyquibbler as qb
    from pyquibbler import iquib
    qb.override_all()
    
    # Other imports:
    import numpy as np
    import matplotlib.pyplot as plt
    %matplotlib tk

.. code:: python

    xy = iquib(np.array([[250], [250]]))
    xy2 = xy + 1000

.. code:: python

    # set the project path to the current directory
    qb.set_project_directory('.')  
    qb.get_project_directory()




.. raw:: html

    <a href="file:///Users/roykishony/pyquibbler/docs">docs</a>



.. code:: python

    qb.get_project().save_format




.. parsed-literal::

    <SaveFormat.VALUE_TXT: 'value_txt'>



.. code:: python

    qb.save_quibs()

.. code:: python

    xy[1,0] = 10

.. code:: python

    xy.get_value()




.. parsed-literal::

    array([[250],
           [ 10]])



