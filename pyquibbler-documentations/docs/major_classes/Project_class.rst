pyquibbler.Project
==================

.. currentmodule:: pyquibbler

.. autoclass:: Project
   :members:
   :show-inheritance:
   :inherited-members:

   
   .. rubric:: Project

   .. autosummary::

      ~Project.get_or_create
      ~Project.quibs


   .. rubric:: Undo/Redo

   .. autosummary::

      ~Project.undo
      ~Project.redo
      ~Project.can_undo
      ~Project.can_redo
      ~Project.clear_undo_and_redo_stacks


   .. rubric:: File syncing

   .. autosummary::

      ~Project.DEFAULT_SAVE_FORMAT
      ~Project.save_format
      ~Project.directory
      ~Project.load_quibs
      ~Project.save_quibs
      ~Project.sync_quibs


   .. rubric:: Reset quibs

   .. autosummary::

      ~Project.reset_file_loading_quibs
      ~Project.reset_impure_quibs
      ~Project.reset_random_quibs


   .. rubric:: Graphics

   .. autosummary::

      ~Project.DEFAULT_GRAPHICS_UPDATE
      ~Project.graphics_update
      ~Project.refresh_graphics

   