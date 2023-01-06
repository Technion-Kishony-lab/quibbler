# Quibbler's Jupyterlab extension

![GitHub](https://img.shields.io/github/license/Technion-Kishony-lab/quibbler)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/Technion-Kishony-lab/quibbler)


Integrate Quibbler's Undo/Redo and Save/Load capabilities within JupyterLab.

![](https://github.com/Technion-Kishony-lab/quibbler/blob/master/pyquibbler-documentations/docs/images/labext_open.png?raw=true)

For a complete guide to using Quibbler within JupyterLab, see [here](https://quibbler.readthedocs.io/en/latest/Jupyter-lab-ext.html).

## Undo / Redo

The extension adds **Undo/Redo** buttons to the JupyterLab toolbar.

Here is and example of how these buttons behave 
(with the
[image thresholding demo](https://quibbler.readthedocs.io/en/latest/examples/quibdemo_image_thresholding.html)):

![](https://github.com/Technion-Kishony-lab/quibbler/blob/master/pyquibbler-documentations/docs/images/labext_undo_redo.gif?raw=true)


## Save / Load
<img src="https://github.com/Technion-Kishony-lab/quibbler/blob/master/pyquibbler-documentations/docs/images/labext_quibbler_menu.png?raw=true" width=250 align='right'>

Assignments to quibs can be saved into the JupyterLab's notebook,
allowing restoring prior values both within the session and when
restarting the notebook as a new session. To enable saving quib assignments into the notebook
check the “Save/Load inside Notebook” option in the JupyterLab
*Quibbler* menu.

Once enabled, quib assignments can easily be saved/loaded, either
globally for the entire notebook by choosing **Save/Load** from the JupyterLab's
**Quibbler** menu, or
individually by clicking the Save/Load buttons at the bottom of the Quib
Editor of the relevant quib, as shown here:

![](https://github.com/Technion-Kishony-lab/quibbler/blob/master/pyquibbler-documentations/docs/images/quib_editor_save_load.gif?raw=true)


## Requirements

* JupyterLab >= 3.0


## Install

To install the extension, execute:

```bash
pip install pyquibbler_labextension
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall pyquibbler_labextension
```


## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the pyquibbler_labextension directory
# Install package in development mode
pip install -e .
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Rebuild extension Typescript source after making changes
jlpm build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

### Development uninstall

```bash
pip uninstall pyquibbler_labextension
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `pyquibbler-labextension` within that folder.

### Packaging the extension

See [RELEASE](RELEASE.md)
