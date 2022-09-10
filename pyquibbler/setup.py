from setuptools import setup, find_packages
from pathlib import Path

setup_directory = Path(__file__).parent
long_description = (setup_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pyquibbler",
    version='0.1.3',
    python_requires='>=3.8',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=["matplotlib==3.4.3",
                      "numpy==1.23.0",
                      "varname==0.8.1",
                      "ipynbname==2021.3.2",
                      "flask==2.1.1",
                      "flask_cors==3.0.10",

                      # We might want to re-consider whether to make these packages a requirement:
                      "ipycytoscape",
                      "ipywidgets",
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
            'interruptingcow',
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
