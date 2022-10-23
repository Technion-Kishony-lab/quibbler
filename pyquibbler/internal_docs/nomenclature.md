## Nomenclature


### Arguments

We separate the arguments to a function are seperated into "Data Arguments", and "Parameter Arguments".
(both can be designated either as part of the args, or kwargs of the function)

#### Data Argument 
Data arguments are arguments whose individual elements (e.g., for arrays, list) only affect the values of 
specific elements in the result. 

#### Parameter Argument
Parameter arguments are arguments whose value affect the result as a whole.

For example. in `np.reshape(data, shape)`, `data` is a data argument and `shape` is a 
parameter argument.  

#### Data Argument Designation: 
The specific data arguments for each function are defined as DataArgumentDesignation, 
as part of the function definition, 

### Sources

Sources are quibs implemented as or within arguments.

#### Parameter Sources
Sources standing as a parameter argument, or within a parameter argument.
Their entire value is required to calculate any part of the function.

#### Major data sources
Sources incorporated as a data argument. 
For example, if `w` is a quib, it serves as a _major data source_ in the function 
`np.sin(w)`. 

#### Sub-major data sources
Sources incorporated as part of a data argument, with their individual elements mapped 
to individual elements of the function result.

For example:
w = iquib([1, 2])
a = np.array([w, [3, 4]])
w is a sub-major data source in this function.
 
* Minor Data Sources: 
Sources that appear in a Data Argument but their value is guaranteed to affect only one element of the result.

For example, The quib `w = iquib([1, 2])` serves as a sub-major data source in the function
`np.array([{'values': w}, {'values': [3, 4]}])`
