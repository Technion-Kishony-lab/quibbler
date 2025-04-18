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

Assignments can be saved as a text file or binary file (``'txt'``,
``'json'``, or ``'bin'``). The file format can be set globally for all
quibs using the Project’s :py:attr:`~pyquibbler.Project.save_format`, or individually for
each quib using the Quib’s :py:attr:`~pyquibbler.Quib.save_format`.

Simple example of assignment saving to file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As a simple example for saving quib assignment to file, conider the
following code:

.. code:: python

    # Quibbler import:
    import pyquibbler as qb
    from pyquibbler import iquib
    qb.initialize_quibbler()
    
    # Other imports:
    import numpy as np
    import matplotlib.pyplot as plt
    %matplotlib tk

.. code:: python

    # set the project path to the current directory
    import os
    os.system('mkdir my_data')
    qb.set_project_directory('my_data')

.. code:: python

    # By default, quibs are saved to text file:
    qb.get_project().save_format




.. code:: none

    <SaveFormat.TXT: 'txt'>



.. code:: python

    # Define an iquib and an fquib:
    xy = iquib([10.5, 17.0])

.. code:: python

    # Make an assignment
    xy[1] = 18.

.. code:: python

    xy.get_value()




.. code:: none

    [10.5, 18.0]



.. code:: python

    # Save all assignments:
    qb.save_quibs()

.. code:: python

    os.system('ls my_data');


.. code:: none

    xy.txt


.. code:: python

    os.system('cat my_data/xy.txt');


.. code:: none

    quib[1] = 18.0

.. code:: python

    xy[1] = 20.
    xy.get_value()




.. code:: none

    [10.5, 20.0]



.. code:: python

    qb.load_quibs()


.. code:: none

    xy
    Data has changed.
    Overwrite assignment?
    1 :  Overwrite
    2 :  Skip


.. code:: none

     1


.. code:: python

    xy.get_value()




.. code:: none

    [10.5, 18.0]



