"""
run this file to convert all examples and doc notebooks to wiki md files.
the created md files are saved in the docs folder for sphinx
as well as copied to pyquibbler.wiki, which is a separate repository
"""


import os
print(os.getcwd())

import glob
from remove_empty_lines_from_md import remove_empty_lines_from_md
from pathlib import Path

sep = os.path.sep

demo_notebooks_path = os.path.join('..', '..', 'examples', 'notebooks')
docs_notebooks_path = os.path.join('..')
wiki_path = os.path.join('..', '..', '..', 'pyquibbler.wiki')
wiki_demo_path = os.path.join(wiki_path, 'examples')
wiki_demo_gif_path = os.path.join(wiki_path, 'images', 'demo_gif')
docs_path = os.path.join('..', '..', 'docs')
docs_demo_path = os.path.join(docs_path, 'examples')
docs_demo_gif_path = os.path.join(docs_path, 'images', 'demo_gif')

Path(docs_demo_path).mkdir(parents=True, exist_ok=True)

# --- wiki ---
if False:
    # convert all demo notebooks to md and move to the wiki_examples_path
    os.system("jupyter nbconvert --to markdown " + demo_notebooks_path + sep + "quibdemo*.ipynb")
    os.system("mv " + demo_notebooks_path + sep + "quibdemo*.md " + wiki_demo_path)

    # For each demo md file, add a link to the corresponding GIF if exists:
    full_files = glob.glob(wiki_demo_path + sep + '*.md')
    for full_file in full_files:
        _, file = os.path.split(full_file)
        file = file[:-3]
        if os.path.isfile(wiki_demo_gif_path + sep + file + ".gif"):
            with open(full_file, "a") as myfile:
                print(file)
                myfile.write("[](/images/demo_gif/" + file + ".gif)")
                myfile.write("")

    # convert docs notebooks to md and move to wiki path:
    os.system("jupyter nbconvert --to markdown " + docs_notebooks_path + "/*.ipynb")
    full_files = glob.glob(docs_notebooks_path + sep + '*.md')
    for full_file in full_files:
        remove_empty_lines_from_md(full_file)
    os.system("mv " + docs_notebooks_path + "/*.md " + wiki_path)


# --- sphinx ---

# convert all demo notebooks rst and move to the doc folder
os.system("jupyter nbconvert --to rst " + demo_notebooks_path + sep + "quibdemo*.ipynb")
os.system("mv " + demo_notebooks_path + sep + "quibdemo*.rst " + docs_demo_path)

# For each demo rst file, add a link to the corresponding GIF if exists:
full_files = glob.glob(docs_demo_path + sep + '*.rst')
for full_file in full_files:
    _, file = os.path.split(full_file)
    file = file[:-4]
    if os.path.isfile(docs_demo_gif_path + sep + file + ".gif"):
        with open(full_file, "a") as myfile:
            print(file)
            myfile.write(".. image:: ../images/demo_gif/" + file + ".gif")
            myfile.write("")

# sed -E 's/Quib.([a-z])/:py:attr:`~pyquibbler.Quib.\1/g'
# echo "(see Quib.func and Quib.get_value()" | sed -Ee 's/Quib.([_[:alnum:]]{1,20}\(\))/:py:meth:`~pyquibbler.Quib.\1/g'

# convert docs notebooks to rst and move to doc folder:
os.system("jupyter nbconvert --to rst " + docs_notebooks_path + "/*.ipynb")
full_files = glob.glob(docs_notebooks_path + sep + '*.rst')
for full_file in full_files:
    os.system(r"sed -i '' -E 's/\[\[Quib\]\]/:py:class:`~pyquibbler.Quib`/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[quibdemo([-_[:alnum:]]{1,100}\]\])/\[\[examples\/quibdemo\1/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[([A-Z,a-z][-_ [:alnum:]]{1,100})\|([-_ [:alnum:]]{1,100})\]\]/:doc:`\1<\2>`/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[([A-Z,a-z][-_ [:alnum:]]{1,100})\]\]/:doc:`\1`/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[Quib.([_[:alnum:]]{1,30})\]\]/:py:attr:`~pyquibbler.Quib.\1`/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[Quib.([_[:alnum:]]{1,30}\(\))\]\]/:py:meth:`~pyquibbler.Quib.\1`/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[qb.([_[:alnum:]]{1,30})\]\]/:py:func:`~pyquibbler.\1`/g' " + full_file)
    os.system(r"sed -i '' -E 's/\[\[[/]images([-/_[:alnum:].]{1,90})\]\]/.. image:: images\1/g' " + full_file)

os.system("mv " + docs_notebooks_path + "/*.rst " + docs_path)
