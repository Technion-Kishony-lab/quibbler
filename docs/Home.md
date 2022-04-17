# Data Quibbler
**Building interactive, traceable, transparent, and efficient data analysis pipelines.** 

## What is it?
*Quibbler* is a toolset for building highly interactive, yet traceable, 
transparent and efficient data analysis pipelines. *Quibbler* allows using standard 
*Python* syntax to process data through any series of analysis steps, while 
automatically maintaining connectivity between downstream results and upstream raw 
sources. *Quibbler* facilitates and embraces human interventions as an inherent part 
of the analysis pipeline: input parameters, as well as exceptions and overrides, 
can be specified and adjusted either programmatically, through input files, or by 
interacting with "live" graphics, and all such interventions are automatically 
recorded in well-documented human-machine readable files. Changes to such parameters 
propagate downstream, pinpointing which specific steps and specific data array or
even specific slices or elements thereof are affected, thereby vastly saving unnecessary 
recalculations. *Quibbler*, therefore, facilitates hands-on interactions with data 
in ways that are flexible and interactive, yet also efficient, traceable, 
well-documented, and reproducible.

## Main Features
Here are a few of the things that *Quibbler* does:


* Easily build powerful GUI-like interaction with data, without a need for callbacks 
and listeners. 

* Interactive specification of inputs and exceptions to default functionalities.

* Automatically maintain a record of user interventions and parameter specifications.

* Independently calculate, cache and validate/invalidate focal elements or slices of heavy-to-calculate arrays. 

* Track a dependency graph between raw data and downstream results.  

* Inherent undo/redo functionalities.

* **All-of-the-above using standard functions and programming syntax - very little to learn to get started!** 


