from setuptools import setup, find_packages
from pathlib import Path

setup_directory = Path(__file__).parent
long_description = (setup_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pyquibbler",
    version='0.1.9',
    python_requires='>=3.8',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=["matplotlib==3.5.3",
                      "numpy==1.23.2",
                      "varname==0.9.0",

                      # TODO: These following packages are not strictly needed.
                      #       They enhance interactive functionality within Jupyter lab.
                      #       We might want to consider whether to define them as "required"
                      "ipynbname==2021.3.2",
                      "flask==2.1.1",
                      "flask_cors==3.0.10",
                      "ipycytoscape==1.3.3",
                      "ipywidgets==8.0.2",
                      "traitlets",
                      "IPython",
                      ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov',
            'pytest-benchmark',
            'selenium',
            'requests',
            'psutil',
            'pytest-benchmark',
        ],
        'sphinx': [
            'sphinx',
            'myst-parser',
            'sphinx_rtd_theme',
        ]
    }
)
