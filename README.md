<img src="https://github.com/Technion-Kishony-lab/quibbler/blob/master/pyquibbler-documentations/docs/images/quibicon.gif?raw=true" width=300 align='right'>

# Quibbler
**Interactive, reproducible and efficient data analytics**

![GitHub](https://img.shields.io/github/license/Technion-Kishony-lab/quibbler)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/Technion-Kishony-lab/quibbler)


## What is it?
*Quibbler* is a toolset for building highly interactive, yet reproducible, 
transparent and efficient data analysis pipelines. *Quibbler* allows using standard 
*Python* syntax to process data through any series of analysis steps, while 
automatically maintaining connectivity between downstream results and upstream raw data 
sources. *Quibbler* facilitates and embraces human interventions as an inherent part 
of the analysis pipeline: input parameters, as well as exceptions and overrides, 
can be specified and adjusted either programmatically, or by 
interacting with "live" graphics, and all such interventions are automatically 
recorded in well-documented human-machine readable files. Changes to such parameters 
propagate downstream, pinpointing which specific data items, or
even specific elements thereof, are affected, thereby vastly saving unnecessary 
recalculations. *Quibbler*, therefore, facilitates hands-on interactions with data 
in ways that are not only flexible, fun and interactive, but also traceable, 
well-documented, and highly efficient.


### "Best Quibble" competition
We just launched *Quibbler* in [PyData Tel-Aviv](https://pydata.org/telaviv2022/).
We are seeking engagement from users and developers and are also eager to learn of 
the range of applications for *Quibbler*. 
To get it fun and going, we are announcing a competition for the best **"Quibble"** - 
a short elegant quib-based code that demonstrates fun interactive graphics and/or hints 
to ideas of applications. 

For details (and prizes!) see: [Best Quibble Award](https://kishony.technion.ac.il/best-quibble-award/)   


## Main Features
<img src="https://github.com/Technion-Kishony-lab/quibbler/blob/master/pyquibbler-documentations/docs/images/quibbler_promo.gif?raw=true" width=300 align='right'>

Here are a few of the things that *Quibbler* does:

* Easily build powerful GUI-like interaction with data, without a need for callbacks 
and event listeners. 

* Interactive specification of inputs and overrides of parameter values.

* Automatically create human-readable records of user interventions and parameter specifications.

* Independently calculate, cache and validate/invalidate individual slices of heavy-to-calculate arrays. 

* Present a dependency graph between raw data and downstream results.  

* Provide inherent undo/redo functionalities.

* **_All-of-the-above using completely standard functions and programming syntax - 
there is very little to learn to get started!_** 


## Documentations
For complete documentations and a getting-started tour, see [readthedocs](https://quibbler.readthedocs.io/en/latest/).


## Installation 

We recommend installing *Quibbler* in a new virtual environment 
(see [creating a new environment](https://github.com/Technion-Kishony-lab/quibbler/blob/master/INSTALL.md)). 

To install run:

`pip install pyquibbler`

If are using *Jupyter lab*, you can also add the *pyquibbler Jupyter Lab extensions*:

`pip install pyquibbler_labextension`

To install for developers, 
see our guide [here](https://github.com/Technion-Kishony-lab/quibbler/blob/master/INSTALL.md).

## Credit

Quibbler was created by Roy Kishony, initially implemented as a Matlab toolbox. 

The first release of Quibbler for Python, *pyquibbler*, was developed at the 
[Kishony lab](https://kishony.technion.ac.il/quibbler/), 
[Technion - Israel Institute of Technology](https://www.technion.ac.il/), 
by Maor Kern, Maor Kleinberger and Roy Kishony.

We very much welcome any thoughts, suggestions and ideas and of course welcome PR contributions 
(for some proposed directions, see our pending [issues](https://github.com/Technion-Kishony-lab/quibbler/issues)). 

## Related products

* [Streamlit](https://streamlit.io/)
* [Plotly](https://plotly.com/)
* [Shiny](https://shiny.rstudio.com/)
* [ipywidgets](https://github.com/jupyter-widgets/ipywidgets)
* [bokeh](http://bokeh.org)
* [Vega-Altair](https://altair-viz.github.io/)
* [Datashader](https://datashader.org/)
