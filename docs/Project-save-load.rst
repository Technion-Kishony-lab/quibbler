Project save/load
-----------------

As we explore data, we often make rational changes to parameters by
overriding the initial values of either input or function quibs. These
overriding assignments can be saved to external files and re-loaded when
the session is initiated. Importantly, overriding assignments can be
saved in simple text human readable/writable files, providing a
transparent record of user defined parameters and changes. The linkage
between a quib and its overriding file is bidirectional - changes to the
quib overriding assignments can be saved to the file, and changes to the
file can be loaded to update the quib.

File names and locations
~~~~~~~~~~~~~~~~~~~~~~~~

By default, quibs save their assignment file to the :py:class:`~pyquibbler.Project`’s
:py:attr:`~pyquibbler.Project.directory`, which can be get/set using the functions
:py:func:`~pyquibbler.get_project_directory` and :py:func:`~pyquibbler.set_project_directory`.

Alternatively, each quib can set its own path, either relative to the
Project directory, or as an absolute path (see :py:attr:`~pyquibbler.Quib.save_directory`).

The name of the file of each quib is defined by its
:py:attr:`~pyquibbler.Quib.assigned_name` (only quibs with defined ``assigned_name`` can
save to a file).

The ultimate file path for each quib is given by the :py:attr:`~pyquibbler.Quib.file_path`
property.

Assignment file format
~~~~~~~~~~~~~~~~~~~~~~

Assignments can be saved as a text file or binary file (see
:py:func:`~pyquibbler.SaveFormat`). The file format can be set globally for all quibs
using the Project’s :py:attr:`~pyquibbler.Project.save_format`, or inidividually for each
quib using the Quib’s [[

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




.. code:: none

    <SaveFormat.VALUE_TXT: 'value_txt'>



.. code:: python

    qb.save_quibs()

.. code:: python

    xy[1,0] = 10

.. code:: python

    xy.get_value()




.. code:: none

    array([[250],
           [ 10]])



