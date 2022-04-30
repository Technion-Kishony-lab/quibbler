"""
run this file to convert all examples and doc notebooks to rst files.
the created rst files are saved in the docs folder for sphinx
"""

import os
from pathlib import Path

sep = os.path.sep

demo_notebooks_path = Path('..', '..', 'examples', 'notebooks')
docs_notebooks_path = Path('..')
docs_path = Path('..', '..', 'docs')
docs_demo_path = docs_path / 'examples'
docs_demo_gif_path = docs_path / 'images' / 'demo_gif'

docs_demo_path.mkdir(parents=True, exist_ok=True)

# convert all demo notebooks to rst and move to the doc folder
os.system(f"jupyter nbconvert --to rst {demo_notebooks_path / 'quibdemo*.ipynb'}")
os.system(f"mv {demo_notebooks_path / 'quibdemo*.rst'}  {docs_demo_path}")

# For each demo rst file, add a link to the corresponding GIF if exists:
rst_paths = docs_demo_path.glob('quibdemo*.rst')
for rst_path in rst_paths:
    gif_file = (docs_demo_gif_path / rst_path.stem).with_suffix('.gif')
    if gif_file.exists():
        with open(rst_path, "a") as rstfile:
            print(f'appending GIF to {rst_path.stem}')
            rstfile.write(f".. image:: ../images/demo_gif/{gif_file.name}\n")


# convert docs notebooks to rst and move to doc folder:
os.system(f"jupyter nbconvert --to rst {docs_notebooks_path / '*.ipynb'}")
rst_paths = docs_notebooks_path.glob('*.rst')
for rst_path in rst_paths:

    file = str(rst_path)
    # [[Quib]] -> `~pyquibbler.Quib`
    os.system(r"sed -i '' -E 's/\[\[Quib\]\]/:py:class:`~pyquibbler.Quib`/g' " + file)

    # [[quibdemoXXX]] -> [[examples/quibdemoXXX]]
    os.system(r"sed -i '' -E 's/\[\[quibdemo([-_[:alnum:]]{1,100}\]\])/\[\[examples\/quibdemo\1/g' " + file)

    # [[see this reference|reference]] -> :doc:`see this reference<reference>`
    os.system(r"sed -i '' -E 's/\[\[([A-Z,a-z][-._ [:alnum:]]{1,100})\|([-.:<>/_ [:alnum:]]{1,100})\]\]/:doc:`\1<\2>`/g' " + file)

    # [[reference]] -> :doc:`reference`
    os.system(r"sed -i '' -E 's/\[\[([A-Z,a-z][-/_ [:alnum:]]{1,100})\]\]/:doc:`\1`/g' " + file)

    # [[Quib.xxx]] -> :py:attr:`~pyquibbler.Quib.xxx`
    os.system(r"sed -i '' -E 's/\[\[Quib.([_[:alnum:]]{1,50})\]\]/:py:attr:`~pyquibbler.Quib.\1`/g' " + file)

    # [[Quib.xxx()]] -> :py:meth:`~pyquibbler.Quib.xxx`
    os.system(r"sed -i '' -E 's/\[\[Quib.([_[:alnum:]]{1,50}\(\))\]\]/:py:meth:`~pyquibbler.Quib.\1`/g' " + file)

    # [[qb.xxx]] -> :py:func:`~pyquibbler.xxx`
    os.system(r"sed -i '' -E 's/\[\[qb.([_[:alnum:]]{1,50})\]\]/:py:func:`~pyquibbler.\1`/g' " + file)

    # [[/imagesXXX]] -> .. image:: imagesXXX
    os.system(r"sed -i '' -E 's/\[\[[/]images([-/_[:alnum:].]{1,90})\]\]/.. image:: images\1/g' " + file)

os.system(f"mv {docs_notebooks_path / '*.rst'} {docs_path}")
