import os
import glob

notebooks_path = '../examples/notebooks'
wiki_examples_path = '../../pyquibbler.wiki/examples'
wiki_gif_path = '../../pyquibbler.wiki/images/demo_gif'

os.system("jupyter nbconvert --to markdown " + notebooks_path + "/quibdemo*.ipynb")
os.system("mv " + notebooks_path + "/quibdemo*.md " + wiki_examples_path)

full_files = glob.glob(wiki_examples_path + '/*.md')
print(full_files)

for full_file in full_files:
    _, file = os.path.split(full_file)
    file = file[:-3]
    if os.path.isfile(wiki_gif_path + '/' + file + ".gif"):
        with open(full_file, "a") as myfile:
            print(file)
            myfile.write("[[/images/demo_gif/" + file + ".gif]]")
            myfile.write("")

