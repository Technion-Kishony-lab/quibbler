from setuptools import setup, find_packages

setup(
    name="pyquibbler",
    version='0.1.3',
    python_requires='>=3.8',
    long_description="Quibbler",
    packages=find_packages(),
    install_requires=["matplotlib==3.4.3",
                      "numpy==1.23.0",
                      "varname==0.8.1",
                      "json-tricks==3.15.5",
                      "ipynbname==2021.3.2",
                      "flask==2.1.1",
                      "flask_cors==3.0.10",
                      "ipycytoscape",
                      ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov',
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
