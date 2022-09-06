## Manual install for development. 

For users, we recommend installing using `pip install` (see [here](INSTALL.md)).


For development, we recommend installing using the `install.py` script 
([here](INSTALL.md)). 

If you instead prefer to install manually, follow these steps: 

#### 1. Create environment:

```conda create -n pyquibbler --override-channels --strict-channel-priority -c conda-forge -c nodefaults jupyterlab=3 cookiecutter nodejs jupyter-packaging git```

```conda activate pyquibbler```

#### 2. Install pyquibbler-labextension:
In the quibbler root directory:

```cd pyquibbler-labextension```

```pip install -e .```

```jupyter labextension develop . --overwrite```

```jlpm run build```

```jupyter lab build --minimize=False```

If you are developing the client code, then to automatically build following changes, run:

```jlpm run watch```


#### 3. Install pyquibbler:

```cd ../pyquibbler```

```pip install -e ".[dev, sphinx]"```

#### 4. Install chromedriver (for lab tests)

If you are developing the *pyquibbler jupyter-lab extension*, to be able to run 
the specific jupyterlab-extension tests, you will also need to install 
`chromedriver` (see [here](tests/lab_extension/README.md)).
