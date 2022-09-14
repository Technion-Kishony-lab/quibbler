pyquibbler.Quib
===============

.. currentmodule:: pyquibbler

.. autoclass:: Quib
   :members: get_value
   :show-inheritance:
   :inherited-members:


   .. rubric:: Function

   .. autosummary::

      ~Quib.func
      ~Quib.args
      ~Quib.kwargs
      ~Quib.is_iquib
      ~Quib.is_graphics
      ~Quib.is_random
      ~Quib.is_file_loading
      ~Quib.is_impure
      ~Quib.pass_quibs


   .. rubric:: Calculate

   .. autosummary::

      ~Quib.get_value
      ~Quib.invalidate
      ~Quib.get_ndim
      ~Quib.get_shape
      ~Quib.get_type
      ~Quib.cache_mode
      ~Quib.cache_status


   .. rubric:: Relationships

   .. autosummary::

      ~Quib.get_children
      ~Quib.get_parents
      ~Quib.get_descendants
      ~Quib.get_ancestors


   .. rubric:: Assignments

   .. autosummary::

      ~Quib.allow_overriding
      ~Quib.assigned_quibs
      ~Quib.assignment_template
      ~Quib.set_assignment_template
      ~Quib.assign
      ~Quib.get_override_list
      ~Quib.get_override_mask


   .. rubric:: File sync

   .. autosummary::

      ~Quib.project
      ~Quib.save_directory
      ~Quib.actual_save_directory
      ~Quib.save_format
      ~Quib.actual_save_format
      ~Quib.file_path
      ~Quib.load
      ~Quib.save
      ~Quib.sync


   .. rubric:: Name and display

   .. autosummary::

      ~Quib.name
      ~Quib.assigned_name
      ~Quib.get_quiby_name
      ~Quib.created_in
      ~Quib.functional_representation
      ~Quib.pretty_repr
      ~Quib.ugly_repr
      ~Quib.display_properties


   .. rubric:: Graphics

   .. autosummary::
   
      ~Quib.graphics_update
      ~Quib.actual_graphics_update
      ~Quib.is_graphics_quib


   .. rubric:: Other

   .. autosummary::

      ~Quib.iter_first
      ~Quib.setp
