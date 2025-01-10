## Building pyquibbler documentations

Documentations are written mostly as Jupyter lab notebooks, 
stored in `./examples` and `./docs_notebooks.`

Run `convert_doc_notebooks_to_rst` to convert the notebooks
into rst files which will be created in the `docs` and `docs/examples`.

There are also `rst` and `md` files in the `docs` folder that are not generated 
from notebooks, and can instead be edited directly:
`index.rst`, `Examples.rst`, `What-is-it.md`,
`Rationale.md`, `Quibbler_Enums.rst`, `List_of_functions.rst`
`Installation.rst`. 

The documentations are built by `readthedocs` with any push to master.

To build the documentations into html locally, run at the project route directory:
`make html`

happy documenting!
