'''
run this file to convert all notebooks to wiki md files.

the crerated md files are saved to pyquibbler.wiki, which is a seperare repository
'''


import os
import glob

sep = os.path.sep

demo_notebooks_path = os.path.join('..', 'examples', 'notebooks')
docs_notebooks_path = os.path.join('..', 'docs')
wiki_path = os.path.join('..', '..', 'pyquibbler.wiki')
wiki_demo_path = os.path.join(wiki_path, 'examples')
wiki_demo_gif_path = os.path.join(wiki_path, 'images', 'demo_gif')

# convert all demo notebooks and move to the wiki_examples_path
os.system("jupyter nbconvert --to markdown " + demo_notebooks_path + sep + "quibdemo*.ipynb")
os.system("mv " + demo_notebooks_path + sep + "quibdemo*.md " + wiki_demo_path)

full_files = glob.glob(wiki_demo_path + sep + '*.md')
print(full_files)

# For each example md file, add a link to the corresponding GIF if exists:
for full_file in full_files:
    _, file = os.path.split(full_file)
    file = file[:-3]
    if os.path.isfile(wiki_demo_gif_path + sep + file + ".gif"):
        with open(full_file, "a") as myfile:
            print(file)
            myfile.write("[[/images/demo_gif/" + file + ".gif]]")
            myfile.write("")

# convert docs notebooks to md and move to wiki path:
os.system("jupyter nbconvert --to markdown " + docs_notebooks_path + "/*.ipynb")
os.system("mv " + docs_notebooks_path + "/*.md " + wiki_path)
