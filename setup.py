from setuptools import setup, find_packages

setup(
    name="pyquibbler",
    version='0.1.0',
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=["matplotlib==3.4.3", "numpy==1.21.2"]
)
