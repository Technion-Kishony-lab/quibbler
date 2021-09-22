# PyQuibbler

## DOC

### Interface

- `iquib`
- `Quib.get_value()`
- `DefaultFunctionQuib.is_cache_valid`
- `Quib.get_caching_method()`
- `Quib.set_caching_method()`

### Debugging

- `FunctionQuib._func`
- `FunctionQuib._args`
- `FunctionQuib._kwargs`
- `FunctionQuib._get_dependencies()`
- `FunctionQuib.get_cache_behavior()`

## Q/A

- Why do changes not occur after doing `plt.show(block=False); # my_stuff; time.sleep(1000)`
  - The event loop needs to run- we tried doing `flush_events` but the only way (we saw on mac)
    for events to happen is to actually start the event loop (this happens automatically when pausing). <br/>
    As a side note, our solution (of ```axes.redraw_in_frame(); axes.figure.canvas.blit()```)
    has near identical performance to running the event loop ) <br/>
    It is important to note that we're not sure of all of this for other backends.

#### Array copy/view behavior
In some cases, an operation on a numpy array can result with a view to that numpy array,
instead of a new array referencing new memory. For example:

- `np.view(arr)`
- `arr[4:10]`
- `arr.reshape((3, 5))`
- `arr.swapaxes((1, 2))`

Some functions can return both a view an a copy, according to the arguments.
For example `__getitem__` will return a copy only if the selected data is contiguous in memory.
On view arrays, the attribute `base` points to the original array instead of `None`.