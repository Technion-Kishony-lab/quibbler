import os
import glob

notebooks_path = '../examples/notebooks'
wiki_path = '../../pyquibbler.wiki/files'

files = glob.glob(notebooks_path + '/*')
print(files)

os.system("jupyter nbconvert --to markdown ../examples/notebooks/*.ipynb")
