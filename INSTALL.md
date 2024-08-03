## Install pyquibbler


### Create a new virtual environment

If you are using conda, we recommend creating a new environment for `pyquibbler` installation.

```conda create --name pyquibbler python=3.11``` 

```conda activate pyquibbler```


### Install for users

You can simply install *pyquibbler* using pip: 

```pip install pyquibbler```


If you have *Jupyter lab*, you can also add the *pyquibbler Jupyter Lab extensions*:

```pip install pyquibbler_labextension```

### Install for development

To install pyquibbler for development, you can use the 'install.py' script. 
Follow these four steps: 

#### 1. Clone pyquibbler from GitHub.

```git clone https://github.com/Technion-Kishony-lab/quibbler```

#### 2. Install Jupyter lab (optional):

```pip install jupyterlab==3.4.7```

#### 3. Run the 'install.py' script: 

```python install.py```

This will install *pyquibbler*, and if *Jupyter Lab* is installed it will also offer 
to install the *pyquibbler Jupyter Lab extension*.      

Note: On *Windows*, if you wish installing the *pyquibbler juputer-lab extension*, you need first to [enable device 
for development](https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development).


#### 4. Install chromedriver (for lab tests)

If you are developing the *pyquibbler jupyter-lab extension*, to be able to run 
the specific jupyterlab-extension tests, you will also need to install 
`chromedriver` (see [here](tests/lab_extension/README.md)).
